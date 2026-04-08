from __future__ import annotations

import base64
import json
from base64 import b64encode
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Literal, overload

from algokit_abi import abi, arc32, arc56
from algokit_common import from_wire


class _ActionType(str, Enum):
    CALL = "CALL"
    CREATE = "CREATE"


_ARG_ALIASES: Mapping[str, arc56.ReferenceType | arc56.TransactionType] = {
    **{r.value: r for r in arc56.ReferenceType},
    **{t.value: t for t in arc56.TransactionType},
}


__all__ = ["arc32_to_arc56"]


def arc32_to_arc56(arc32_application_spec: str | arc32.Arc32Contract) -> arc56.Arc56Contract:
    """Convert an ARC-32 application specification to ARC-56."""

    arc32_json = (
        arc32_application_spec.to_json()
        if isinstance(arc32_application_spec, arc32.Arc32Contract)
        else arc32_application_spec
    )
    return _Arc32ToArc56Converter(arc32_json).convert()


class _Arc32ToArc56Converter:
    def __init__(self, arc32_application_spec: str):
        self.arc32 = json.loads(arc32_application_spec)

    def convert(self) -> arc56.Arc56Contract:
        source_data = self.arc32.get("source")
        methods, structs = self._convert_methods(self.arc32)
        return arc56.Arc56Contract(
            name=self.arc32["contract"]["name"],
            desc=self.arc32["contract"].get("desc"),
            arcs=[],
            methods=methods,
            structs=structs,
            state=self._convert_state(self.arc32),
            source=arc56.Source(**source_data) if source_data else None,
            bare_actions=arc56.Actions(
                call=self._convert_actions(self.arc32.get("bare_call_config"), _ActionType.CALL),
                create=self._convert_actions(self.arc32.get("bare_call_config"), _ActionType.CREATE),
            ),
        )

    def _convert_storage_keys(self, schema: dict) -> dict[str, arc56.StorageKey]:
        """Convert ARC32 schema declared fields to ARC56 storage keys."""

        return {
            name: arc56.StorageKey(
                key=b64encode(field["key"].encode()).decode(),
                _key_type=arc56.AVMType.STRING,
                _value_type=arc56.AVMType.UINT64 if field["type"] == "uint64" else arc56.AVMType.BYTES,
                desc=field.get("descr"),
            )
            for name, field in schema.items()
        }

    def _convert_state(self, arc32: dict) -> arc56.State:
        """Convert ARC32 state and schema to ARC56 state specification."""
        state_data = arc32.get("state", {})
        return arc56.State(
            schema=arc56.Schema(
                global_state=arc56.Global(
                    ints=state_data.get("global", {}).get("num_uints", 0),
                    bytes=state_data.get("global", {}).get("num_byte_slices", 0),
                ),
                local_state=arc56.Local(
                    ints=state_data.get("local", {}).get("num_uints", 0),
                    bytes=state_data.get("local", {}).get("num_byte_slices", 0),
                ),
            ),
            keys=arc56.Keys(
                global_state=self._convert_storage_keys(arc32.get("schema", {}).get("global", {}).get("declared", {})),
                local_state=self._convert_storage_keys(arc32.get("schema", {}).get("local", {}).get("declared", {})),
                box={},
            ),
            maps=arc56.Maps(global_state={}, local_state={}, box={}),
        )

    def _convert_default_value(self, default_arg: dict[str, Any] | None) -> arc56.DefaultValue | None:
        """Convert ARC32 default argument to ARC56 format."""
        if not default_arg or not default_arg.get("source"):
            return None

        source_mapping = {
            "constant": "literal",
            "global-state": "global",
            "local-state": "local",
            "abi-method": "method",
        }

        mapped_source = source_mapping.get(default_arg["source"])
        if not mapped_source:
            return None
        arg_data = default_arg["data"]
        if mapped_source == "method":
            method = from_wire(arc56.Method, arg_data)
            return arc56.DefaultValue(
                source=mapped_source,  # type: ignore[arg-type]
                data=method.signature,
            )

        default_value_type: abi.ABIType | arc56.AVMType | None = None
        if mapped_source == "literal":
            if isinstance(arg_data, int):
                default_value_type = abi.UintType(64)
                arg_data = default_value_type.encode(arg_data)
            elif isinstance(arg_data, str):
                default_value_type = arc56.AVMType.STRING
            else:
                raise ValueError(f"Invalid default argument data type: {type(arg_data)}")
        if isinstance(arg_data, str):
            arg_data = arg_data.encode("utf-8")
        return arc56.DefaultValue(
            source=mapped_source,  # type: ignore[arg-type]
            data=base64.b64encode(arg_data).decode("utf-8"),
            type=default_value_type,
        )

    @overload
    def _convert_actions(self, config: dict | None, action_type: Literal[_ActionType.CALL]) -> list[arc56.CallEnum]: ...

    @overload
    def _convert_actions(
        self, config: dict | None, action_type: Literal[_ActionType.CREATE]
    ) -> list[arc56.CreateEnum]: ...

    def _convert_actions(
        self, config: dict | None, action_type: _ActionType
    ) -> Sequence[arc56.CallEnum | arc56.CreateEnum]:
        """Extract supported actions from call config."""
        if not config:
            return []

        actions = list[arc56.CallEnum | arc56.CreateEnum]()
        mappings = {
            "no_op": (arc56.CallEnum.NO_OP, arc56.CreateEnum.NO_OP),
            "opt_in": (arc56.CallEnum.OPT_IN, arc56.CreateEnum.OPT_IN),
            "close_out": (arc56.CallEnum.CLOSE_OUT, None),
            "delete_application": (arc56.CallEnum.DELETE_APPLICATION, arc56.CreateEnum.DELETE_APPLICATION),
            "update_application": (arc56.CallEnum.UPDATE_APPLICATION, None),
        }

        for action, (call_enum, create_enum) in mappings.items():
            if action in config and config[action] in ["ALL", action_type]:
                if action_type == "CALL" and call_enum:
                    actions.append(call_enum)
                elif action_type == "CREATE" and create_enum:
                    actions.append(create_enum)

        return actions

    def _convert_method_actions(self, hint: dict | None) -> arc56.Actions:
        """Convert method call config to ARC56 actions."""
        config = hint.get("call_config", {}) if hint else {}
        return arc56.Actions(
            call=self._convert_actions(config, _ActionType.CALL),
            create=self._convert_actions(config, _ActionType.CREATE),
        )

    def _convert_methods(self, arc32: dict) -> tuple[list[arc56.Method], dict[str, abi.StructType]]:
        """Convert ARC32 methods to ARC56 format."""
        methods = []
        contract = arc32["contract"]
        hints = arc32.get("hints", {})
        structs = {}
        for method in contract["methods"]:
            args_sig = ",".join(a["type"] for a in method["args"])
            signature = f"{method['name']}({args_sig}){method['returns']['type']}"
            hint = hints.get(signature, {})
            method_structs = hint.get("structs", {})
            method_args = []
            for arg in method["args"]:
                name = arg.get("name")
                struct_name = None
                if struct := method_structs.get(name):
                    struct_type = _convert_struct(struct)
                    struct_name = struct_type.display_name
                    structs[struct_name] = struct_type
                    arg_type: abi.ABIType | arc56.ReferenceType | arc56.TransactionType = struct_type
                elif alias := _ARG_ALIASES.get(arg["type"]):
                    arg_type = alias
                else:
                    arg_type = abi.ABIType.from_string(arg["type"])
                method_args.append(
                    arc56.Argument(
                        type=arg_type,
                        name=name,
                        desc=arg.get("desc"),
                        default_value=self._convert_default_value(
                            hint.get("default_arguments", {}).get(arg.get("name"))
                        ),
                        struct=struct_name,
                    )
                )
            returns = method["returns"]
            struct_name = None
            if struct := method_structs.get("output"):
                struct_type = _convert_struct(struct)
                struct_name = struct_type.display_name
                structs[struct_name] = struct_type
                return_type: abi.ABIType | arc56.VoidType = struct_type
            elif returns["type"] == arc56.Void:
                return_type = arc56.Void
            else:
                return_type = abi.ABIType.from_string(returns["type"])
            methods.append(
                arc56.Method(
                    name=method["name"],
                    desc=method.get("desc"),
                    readonly=hint.get("read_only"),
                    args=method_args,
                    returns=arc56.Returns(
                        return_type,
                        desc=returns.get("desc"),
                        struct=struct_name,
                    ),
                    actions=self._convert_method_actions(hint),
                    events=[],  # ARC32 doesn't specify events
                )
            )
        return methods, structs


def _convert_struct(struct: dict) -> abi.StructType:
    fields = {name: abi.ABIType.from_string(typ) for name, typ in struct["elements"]}
    return abi.StructType(struct_name=struct["name"], fields=fields)
