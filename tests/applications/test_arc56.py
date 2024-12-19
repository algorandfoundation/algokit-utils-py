from pathlib import Path

from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from tests.conftest import check_output_stability
from tests.utils import load_arc32_spec

TEST_ARC32_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "hello_world" / "arc32_app_spec.json"


def test_from_arc32() -> None:
    arc32_app_spec = load_arc32_spec(
        TEST_ARC32_SPEC_FILE_PATH, deletable=True, updatable=True, template_values={"VERSION": 1}
    )

    arc56_app_spec = Arc56Contract.from_arc32(arc32_app_spec)

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json())
