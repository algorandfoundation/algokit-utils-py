import base64
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import TypeAlias

from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.box_reference import BoxReference as AlgosdkBoxReference

__all__ = [
    "BoxIdentifier",
    "BoxName",
    "BoxReference",
    "BoxValue",
    "DataTypeFlag",
    "TealTemplateParams",
]


@dataclass(kw_only=True, frozen=True)
class BoxName:
    """The name of the box"""

    name: str
    """The name of the box as a string.
    If the name can't be decoded from UTF-8, the string representation of the bytes is returned instead."""
    name_raw: bytes
    """The name of the box as raw bytes"""
    name_base64: str
    """The name of the box as a base64 encoded string"""


@dataclass(kw_only=True, frozen=True)
class BoxValue:
    """The value of the box"""

    name: BoxName
    """The name of the box"""
    value: bytes
    """The value of the box as raw bytes"""


class DataTypeFlag(IntEnum):
    BYTES = 1
    UINT = 2


TealTemplateParams: TypeAlias = Mapping[str, str | int | bytes] | dict[str, str | int | bytes]


BoxIdentifier: TypeAlias = str | bytes | AccountTransactionSigner


class BoxReference(AlgosdkBoxReference):
    def __init__(self, app_id: int, name: bytes | str):
        super().__init__(app_index=app_id, name=self._b64_decode(name))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (BoxReference | AlgosdkBoxReference)):
            return self.app_index == other.app_index and self.name == other.name
        return False

    def _b64_decode(self, value: str | bytes) -> bytes:
        if isinstance(value, str):
            try:
                return base64.b64decode(value)
            except Exception:
                return value.encode("utf-8")
        return value
