from dataclasses import dataclass
from typing import TypeAlias

import algosdk
from algosdk.abi.method import Method

from algokit_utils.models.application import StructField
from algokit_utils.models.state import BoxName

ABIPrimitiveValue = bool | int | str | bytes | bytearray

# NOTE: This is present in js-algorand-sdk, but sadly not in untyped py-algorand-sdk
ABIValue: TypeAlias = ABIPrimitiveValue | list["ABIValue"] | tuple["ABIValue"] | dict[str, "ABIValue"]
ABIStruct: TypeAlias = dict[str, list[StructField]]


ABIType: TypeAlias = algosdk.abi.ABIType


@dataclass(kw_only=True)
class ABIReturn:
    raw_value: bytes | None = None
    value: ABIValue | None = None
    method: Method | None = None
    decode_error: Exception | None = None

    @property
    def is_success(self) -> bool:
        """Returns True if the ABI call was successful (no decode error)"""
        return self.decode_error is None


@dataclass(kw_only=True, frozen=True)
class BoxABIValue:
    name: BoxName
    value: ABIValue
