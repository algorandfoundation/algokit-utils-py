import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[3]
TS_TEST_DATA = (
    ROOT / "references" / "algokit-core" / "packages" / "typescript" / "algokit_transact" / "tests" / "test_data.json"
)


def load_ts_case(case_key: str) -> Mapping[str, Any]:
    data = cast(dict[str, Any], json.loads(TS_TEST_DATA.read_text()))
    return cast(Mapping[str, Any], data[case_key])


def as_bytes(arr: list[int]) -> bytes:
    return bytes(arr)
