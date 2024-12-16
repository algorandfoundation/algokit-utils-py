import base64
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import TypeAlias

from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.box_reference import BoxReference as AlgosdkBoxReference


@dataclass(kw_only=True, frozen=True)
class BoxName:
    name: str
    name_raw: bytes
    name_base64: str


@dataclass(kw_only=True, frozen=True)
class BoxValue:
    name: BoxName
    value: bytes


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
