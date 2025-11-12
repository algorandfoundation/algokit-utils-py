from collections import defaultdict
from pathlib import Path
from typing import Any, ClassVar

import jinja2

from oas_generator import models as ctx
from oas_generator.config import GeneratorConfig
from oas_generator.renderer.filters import (
    descriptor_literal,
    docstring,
    optional_hint,
    response_decode_arguments,
)


class TemplateRenderer:
    BLOCK_MODEL_EXPORTS: ClassVar[list[str]] = [
        "BlockEvalDelta",
        "BlockStateDelta",
        "BlockAccountStateDelta",
        "BlockAppEvalDelta",
        "BlockStateProofTrackingData",
        "BlockStateProofTracking",
        "SignedTxnInBlock",
        "Block",
        "GetBlock",
    ]
    LEDGER_STATE_DELTA_EXPORTS: ClassVar[list[str]] = [
        "LedgerTealValue",
        "LedgerStateSchema",
        "LedgerAppParams",
        "LedgerAppLocalState",
        "LedgerAppLocalStateDelta",
        "LedgerAppParamsDelta",
        "LedgerAppResourceRecord",
        "LedgerAssetHolding",
        "LedgerAssetHoldingDelta",
        "LedgerAssetParams",
        "LedgerAssetParamsDelta",
        "LedgerAssetResourceRecord",
        "LedgerVotingData",
        "LedgerAccountBaseData",
        "LedgerAccountData",
        "LedgerBalanceRecord",
        "LedgerAccountDeltas",
        "LedgerKvValueDelta",
        "LedgerIncludedTransactions",
        "LedgerModifiedCreatable",
        "LedgerAlgoCount",
        "LedgerAccountTotals",
        "LedgerStateDelta",
    ]

    def __init__(self, template_dir: Path | None = None) -> None:
        if template_dir:
            loader: jinja2.BaseLoader = jinja2.FileSystemLoader(str(template_dir))
        else:
            loader = jinja2.PackageLoader("oas_generator.renderer", "templates")
        self.env = jinja2.Environment(
            loader=loader,
            autoescape=False,
            trim_blocks=False,
            lstrip_blocks=False,
        )
        self.env.filters["docstring"] = docstring
        self.env.filters["descriptor_literal"] = descriptor_literal
        self.env.filters["optional_hint"] = optional_hint
        self.env.filters["response_decode_arguments"] = response_decode_arguments

    def render(self, client: ctx.ClientDescriptor, config: GeneratorConfig) -> dict[Path, str]:
        target = config.target_package_dir
        context = self._build_context(client, config)
        files: dict[Path, str] = {}
        files[target / "__init__.py"] = self._render_template("package_init.py.j2", context)
        files[target / "config.py"] = self._render_template("config.py.j2", context)
        files[target / "exceptions.py"] = self._render_template("exceptions.py.j2", context)
        files[target / "types.py"] = self._render_template("types.py.j2", context)
        files[target / "client.py"] = self._render_template("client.py.j2", context)
        models_dir = target / "models"
        files[models_dir / "__init__.py"] = self._render_template("models/__init__.py.j2", context)
        files[models_dir / "_serde_helpers.py"] = self._render_template("models/_serde_helpers.py.j2", context)
        for model in context["client"].models:
            if context["client"].include_ledger_state_delta_models and model.name == "LedgerStateDelta":
                continue
            model_context = {**context, "model": model}
            files[models_dir / f"{model.module_name}.py"] = self._render_template("models/model.py.j2", model_context)
        for enum in context["client"].enums:
            enum_context = {**context, "enum": enum}
            files[models_dir / f"{enum.module_name}.py"] = self._render_template("models/enum.py.j2", enum_context)
        for alias in context["client"].aliases:
            alias_context = {**context, "alias": alias}
            files[models_dir / f"{alias.module_name}.py"] = self._render_template(
                "models/type_alias.py.j2", alias_context
            )
        if client.include_block_models:
            files[models_dir / "_block.py"] = self._render_template("models/block.py.j2", context)
        if client.include_ledger_state_delta_models:
            files[models_dir / "_ledger_state_delta.py"] = self._render_template(
                "models/ledger_state_delta.py.j2", context
            )
        files[target / "py.typed"] = ""
        return files

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)

    def _build_context(self, client: ctx.ClientDescriptor, config: GeneratorConfig) -> dict[str, Any]:
        model_exports = [model.name for model in client.models]
        model_exports.extend(enum.name for enum in client.enums)
        model_exports.extend(alias.name for alias in client.aliases)
        if client.uses_signed_transaction:
            model_exports.append("SignedTransaction")
        if client.include_block_models:
            for name in self.BLOCK_MODEL_EXPORTS:
                if name not in model_exports:
                    model_exports.append(name)
        if client.include_ledger_state_delta_models:
            for name in self.LEDGER_STATE_DELTA_EXPORTS:
                if name not in model_exports:
                    model_exports.append(name)
        metadata_usage = self._collect_metadata_usage(client)
        model_modules = [{"module": model.module_name, "name": model.name} for model in client.models]
        enum_modules = [{"module": enum.module_name, "name": enum.name} for enum in client.enums]
        alias_modules = [{"module": alias.module_name, "name": alias.name} for alias in client.aliases]
        needs_literal = any(
            (op.format_options and len(op.format_options) > 1) for group in client.groups for op in group.operations
        )
        return {
            "client": client,
            "config": config,
            "model_exports": sorted(model_exports),
            "model_modules": model_modules,
            "enum_modules": enum_modules,
            "alias_modules": alias_modules,
            "needs_model_sequence": metadata_usage["model_sequence"],
            "needs_enum_sequence": metadata_usage["enum_sequence"],
            "needs_enum_value": metadata_usage["enum_value"],
            "needs_datetime": any(model.requires_datetime for model in client.models),
            "client_needs_datetime": self._client_requires_datetime(client),
            "block_exports": self.BLOCK_MODEL_EXPORTS,
            "ledger_state_delta_exports": self.LEDGER_STATE_DELTA_EXPORTS,
            "needs_literal": needs_literal,
        }

    def _collect_metadata_usage(self, client: ctx.ClientDescriptor) -> dict[str, bool]:
        flags = defaultdict(bool)
        for model in client.models:
            for field in model.fields:
                expr = field.metadata
                if "encode_model_sequence" in expr:
                    flags["model_sequence"] = True
                if "encode_enum_sequence" in expr:
                    flags["enum_sequence"] = True
                if "enum_value" in expr:
                    flags["enum_value"] = True
        return flags

    def _client_requires_datetime(self, client: ctx.ClientDescriptor) -> bool:
        for group in client.groups:
            for op in group.operations:
                for param in op.parameters:
                    if "datetime" in param.type_hint:
                        return True
                if op.request_body and op.request_body.type_hint and "datetime" in op.request_body.type_hint:
                    return True
                if op.response and op.response.type_hint and "datetime" in op.response.type_hint:
                    return True
        return False
