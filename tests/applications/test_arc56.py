import json
from pathlib import Path

from algokit_abi import arc32_to_arc56, arc56
from tests.conftest import check_output_stability
from tests.utils import load_app_spec

TEST_ARC32_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "hello_world" / "app_spec.arc32.json"
TEST_ARC56_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "amm_arc56_example" / "amm.arc56.json"
TEST_STATE_ARC56_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "state_contract" / "State.arc56.json"
TEST_STATE_ARC32_SPEC_FILE_PATH = Path(__file__).parent.parent / "artifacts" / "state_contract" / "State.arc32.json"


def test_arc56_from_arc32_json() -> None:
    arc56_app_spec = arc32_to_arc56(TEST_ARC32_SPEC_FILE_PATH.read_text())

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))


def test_arc56_from_arc32_instance() -> None:
    arc32_app_spec = load_app_spec(
        TEST_ARC32_SPEC_FILE_PATH, arc=32, deletable=True, updatable=True, template_values={"VERSION": 1}
    )

    arc56_app_spec = arc32_to_arc56(arc32_app_spec)

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))


def test_arc56_from_json() -> None:
    arc56_app_spec = arc56.Arc56Contract.from_json(TEST_ARC56_SPEC_FILE_PATH.read_text())

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))


def test_arc56_from_dict() -> None:
    arc56_app_spec = arc56.Arc56Contract.from_dict(json.loads(TEST_ARC56_SPEC_FILE_PATH.read_text()))

    assert arc56_app_spec

    check_output_stability(arc56_app_spec.to_json(indent=4))


def test_arc32_state_keys_are_not_normalized() -> None:
    arc56_auto_converted_app_spec = arc32_to_arc56(TEST_STATE_ARC32_SPEC_FILE_PATH.read_text())
    raw_app_spec = json.loads(TEST_STATE_ARC32_SPEC_FILE_PATH.read_text())
    assert "bytesNotInSnakeCase" in raw_app_spec["schema"]["global"]["declared"]
    assert "localBytesNotInSnakeCase" in raw_app_spec["schema"]["local"]["declared"]

    assert arc56_auto_converted_app_spec
    assert "bytesNotInSnakeCase" in arc56_auto_converted_app_spec.state.keys.global_state
    assert "localBytesNotInSnakeCase" in arc56_auto_converted_app_spec.state.keys.local_state
    exported_raw_app_spec = json.loads(arc56_auto_converted_app_spec.to_json(indent=4))

    assert "bytesNotInSnakeCase" in exported_raw_app_spec["state"]["keys"]["global"]
    assert "localBytesNotInSnakeCase" in exported_raw_app_spec["state"]["keys"]["local"]

    check_output_stability(arc56_auto_converted_app_spec.to_json(indent=4))


def test_arc56_state_keys_are_not_normalized() -> None:
    arc56_app_spec = arc56.Arc56Contract.from_json(TEST_STATE_ARC56_SPEC_FILE_PATH.read_text())
    raw_app_spec = json.loads(TEST_STATE_ARC56_SPEC_FILE_PATH.read_text())
    assert "bytesNotInSnakeCase" in raw_app_spec["state"]["keys"]["global"]
    assert "localBytesNotInSnakeCase" in raw_app_spec["state"]["keys"]["local"]
    assert "boxMapNotInSnakeCase" in raw_app_spec["state"]["maps"]["box"]
    assert "boxNotInSnakeCase" in raw_app_spec["state"]["keys"]["box"]

    assert arc56_app_spec
    assert "bytesNotInSnakeCase" in arc56_app_spec.state.keys.global_state
    assert "localBytesNotInSnakeCase" in arc56_app_spec.state.keys.local_state
    assert "boxNotInSnakeCase" in arc56_app_spec.state.keys.box
    assert "boxMapNotInSnakeCase" in arc56_app_spec.state.maps.box

    exported_raw_app_spec = json.loads(arc56_app_spec.to_json(indent=4))

    assert "bytesNotInSnakeCase" in exported_raw_app_spec["state"]["keys"]["global"]
    assert "localBytesNotInSnakeCase" in exported_raw_app_spec["state"]["keys"]["local"]
    assert "boxNotInSnakeCase" in exported_raw_app_spec["state"]["keys"]["box"]
    assert "boxMapNotInSnakeCase" in exported_raw_app_spec["state"]["maps"]["box"]

    check_output_stability(arc56_app_spec.to_json(indent=4))
