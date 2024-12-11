from pathlib import Path

from algokit_utils.applications.utils import arc32_to_arc56
from tests.utils import load_arc32_spec

TEST_ARC32_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "hello_world" / "arc32_app_spec.json"


def test_arc32_to_arc56() -> None:
    arc32_app_spec = load_arc32_spec(
        TEST_ARC32_SPEC_FILE_PATH, deletable=True, updatable=True, template_values={"VERSION": 1}
    )

    arc56_app_spec = arc32_to_arc56(arc32_app_spec)

    assert arc56_app_spec
