# src/algokit_utils/models/state.py
from typing import Any, TypedDict


class BoxName(TypedDict):
    name: str
    name_raw: bytes
    name_base64: str


class BoxValue(TypedDict):
    value: bytes


class AppState(dict[str, Any]):
    pass
