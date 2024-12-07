from typing import TypeAlias

import algosdk

from algokit_utils.models.application import StructField

ABIPrimitiveValue = bool | int | str | bytes | bytearray

# NOTE: This is present in js-algorand-sdk, but sadly not in untyped py-algorand-sdk
ABIValue: TypeAlias = ABIPrimitiveValue | list["ABIValue"] | tuple["ABIValue"] | dict[str, "ABIValue"]
ABIStruct: TypeAlias = dict[str, list[StructField]]


ABIType: TypeAlias = algosdk.abi.ABIType
