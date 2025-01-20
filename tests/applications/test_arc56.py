import json
from pathlib import Path

from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from tests.conftest import check_output_stability
from tests.utils import load_app_spec

TEST_ARC32_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "hello_world" / "app_spec.arc32.json"
TEST_ARC56_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "amm_arc56_example" / "amm.arc56.json"


def test_arc56_from_arc32_json() -> None:
    arc56_app_spec = Arc56Contract.from_arc32(TEST_ARC32_SPEC_FILE_PATH.read_text())

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))


def test_arc56_from_arc32_instance() -> None:
    arc32_app_spec = load_app_spec(
        TEST_ARC32_SPEC_FILE_PATH, arc=32, deletable=True, updatable=True, template_values={"VERSION": 1}
    )

    arc56_app_spec = Arc56Contract.from_arc32(arc32_app_spec)

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))


def test_arc56_from_json() -> None:
    arc56_app_spec = Arc56Contract.from_json(TEST_ARC56_SPEC_FILE_PATH.read_text())

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))


def test_arc56_from_dict() -> None:
    arc56_app_spec = Arc56Contract.from_dict(json.loads(TEST_ARC56_SPEC_FILE_PATH.read_text()))

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))
