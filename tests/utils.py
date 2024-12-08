from pathlib import Path

from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.models.application import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME


def load_arc32_spec(
    path: Path,
    *,
    updatable: bool | None = None,
    deletable: bool | None = None,
    template_values: dict | None = None,
) -> ApplicationSpecification:
    spec = ApplicationSpecification.from_json(path.read_text(encoding="utf-8"))

    template_variables = template_values or {}
    if updatable is not None:
        template_variables["UPDATABLE"] = int(updatable)

    if deletable is not None:
        template_variables["DELETABLE"] = int(deletable)

    spec.approval_program = (
        AppManager.replace_template_variables(spec.approval_program, template_variables)
        .replace(f"// {UPDATABLE_TEMPLATE_NAME}", "// updatable")
        .replace(f"// {DELETABLE_TEMPLATE_NAME}", "// deletable")
    )
    return spec
