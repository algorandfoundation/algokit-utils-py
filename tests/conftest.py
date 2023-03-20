import inspect
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from algokit_utils.app import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME, replace_template_variables
from algokit_utils.application_specification import ApplicationSpecification
from dotenv import load_dotenv


@pytest.fixture(autouse=True, scope="session")
def environment_fixture():
    env_path = Path(__file__).parent / ".." / "example.env"
    load_dotenv(env_path)


def check_output_stability(logs: str, *, test_name: str = None) -> None:
    """Test that the contract output hasn't changed for an Application, using git diff"""
    caller_frame = inspect.stack()[1]
    caller_path = Path(caller_frame.filename).resolve()
    caller_dir = caller_path.parent
    test_name = test_name or caller_frame.function
    caller_stem = Path(caller_frame.filename).stem
    output_dir = caller_dir / f"{caller_stem}.approvals"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{test_name}.approved.txt"
    output_file_str = str(output_file)
    output_file_did_exist = output_file.exists()
    output_file.write_text(logs, encoding="utf-8")

    git_diff = subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            "--no-ext-diff",
            "--no-color",
            output_file_str,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # first fail if there are any changes to already committed files, you must manually add them in that case
    assert git_diff.returncode == 0, git_diff.stdout

    # if first time running, fail in case of accidental change to output directory
    if not output_file_did_exist:
        pytest.fail(
            f"New output folder created at {output_file_str} from test {test_name} - "
            "if this was intentional, please commit the files to the git repo"
        )


def read_spec(path: str, *, updatable: bool | None = None, deletable: bool | None = None) -> ApplicationSpecification:
    path = Path(__file__).parent / path
    spec = ApplicationSpecification.from_json(Path(path).read_text(encoding="utf-8"))

    template_variables = {}
    if updatable is not None:
        template_variables["UPDATABLE"] = int(updatable)

    if deletable is not None:
        template_variables["DELETABLE"] = int(deletable)

    spec.approval_program = (
        replace_template_variables(spec.approval_program, template_variables)
        .replace(f"// {UPDATABLE_TEMPLATE_NAME}", "// updatable")
        .replace(f"// {DELETABLE_TEMPLATE_NAME}", "// deletable")
    )
    return spec


def get_specs(
    *, updatable: bool = False, deletable: bool = False
) -> tuple[ApplicationSpecification, ApplicationSpecification, ApplicationSpecification]:
    specs = (
        read_spec("app_v1.json", updatable=updatable, deletable=deletable),
        read_spec("app_v2.json", updatable=updatable, deletable=deletable),
        read_spec("app_v3.json", updatable=updatable, deletable=deletable),
    )
    return specs


def get_unique_name() -> str:
    name = str(uuid4()).replace("-", "")
    assert name.isalnum()
    return name
