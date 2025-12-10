from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import TypeAlias

from algokit_transact import BoxReference as AlgoKitTransactBoxReference
from algokit_transact.signer import AddressWithTransactionSigner

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


BoxIdentifier: TypeAlias = str | bytes | AddressWithTransactionSigner


BoxReference = AlgoKitTransactBoxReference
