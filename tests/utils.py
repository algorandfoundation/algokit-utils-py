from pathlib import Path
from typing import Literal, overload

from algokit_utils.applications.app_manager import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME, AppManager
from algokit_utils.applications.app_spec import Arc32Contract, Arc56Contract


@overload
def load_app_spec(
    path: Path,
    arc: Literal[32],
    *,
    updatable: bool | None = None,
    deletable: bool | None = None,
    template_values: dict | None = None,
) -> Arc32Contract: ...


@overload
def load_app_spec(
    path: Path,
    arc: Literal[56],
    *,
    updatable: bool | None = None,
    deletable: bool | None = None,
    template_values: dict | None = None,
) -> Arc56Contract: ...


def load_app_spec(
    path: Path,
    arc: Literal[32, 56],
    *,
    updatable: bool | None = None,
    deletable: bool | None = None,
    template_values: dict | None = None,
) -> Arc32Contract | Arc56Contract:
    arc_class = Arc32Contract if arc == 32 else Arc56Contract
    spec = arc_class.from_json(path.read_text(encoding="utf-8"))

    template_variables = template_values or {}
    if updatable is not None:
        template_variables["UPDATABLE"] = int(updatable)

    if deletable is not None:
        template_variables["DELETABLE"] = int(deletable)

    if isinstance(spec, Arc32Contract):
        spec.approval_program = (
            AppManager.replace_template_variables(spec.approval_program, template_variables)
            .replace(f"// {UPDATABLE_TEMPLATE_NAME}", "// updatable")
            .replace(f"// {DELETABLE_TEMPLATE_NAME}", "// deletable")
        )
    return spec
