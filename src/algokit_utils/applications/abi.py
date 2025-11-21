from __future__ import annotations

import typing
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias

import algosdk.abi
from algosdk.atomic_transaction_composer import ABIResult

import algokit_abi
from algokit_utils.applications.app_spec import arc56

if TYPE_CHECKING:
    from algokit_utils.models.state import BoxName

ABIValue: TypeAlias = (
    bool | int | str | bytes | bytearray | list["ABIValue"] | tuple["ABIValue"] | dict[str, "ABIValue"]
)
ABIStruct: TypeAlias = dict[str, list[dict[str, "ABIValue"]]]
Arc56ReturnValueType: TypeAlias = ABIValue | ABIStruct | None

ABIType: TypeAlias = algokit_abi.ABIType
ABIArgumentType: TypeAlias = algokit_abi.ABIType | arc56.TransactionType | arc56.ReferenceType

__all__ = [
    "ABIArgumentType",
    "ABIReturn",
    "ABIStruct",
    "ABIType",
    "ABIValue",
    "Arc56ReturnValueType",
    "BoxABIValue",
    "get_abi_decoded_value",
    "get_abi_encoded_value",
    "get_arc56_value",
    "prepare_value_for_atc",
]


@dataclass(kw_only=True)
class ABIReturn:
    """Represents the return value from an ABI method call.

    Wraps the raw return value and decoded value along with any decode errors.
    """

    raw_value: bytes | None = None
    """The raw return value from the method call"""
    value: ABIValue | None = None
    """The decoded return value from the method call"""
    # TODO: replace with arc56 method
    method: algosdk.abi.Method | None = None
    """The ABI method definition"""
    decode_error: Exception | None = None
    """The exception that occurred during decoding, if any"""
    tx_info: dict[str, Any] | None = None
    """The transaction info for the method call from raw algosdk `ABIResult`"""

    def __init__(self, result: ABIResult) -> None:
        self.decode_error = result.decode_error
        if not self.decode_error:
            self.raw_value = result.raw_value
            self.value = result.return_value
            self.method = result.method
            self.tx_info = result.tx_info

    @property
    def is_success(self) -> bool:
        """Returns True if the ABI call was successful (no decode error)

        :return: True if no decode error occurred, False otherwise
        """
        return self.decode_error is None

    def get_arc56_value(self, method: arc56.Method) -> Arc56ReturnValueType:
        """Gets the ARC-56 formatted return value.

        :param method: The ABI method definition
        :return: The decoded return value in ARC-56 format
        """
        return get_arc56_value(self, method)


def get_arc56_value(abi_return: ABIReturn, method: arc56.Method) -> Arc56ReturnValueType:
    """Gets the ARC-56 formatted return value from an ABI return.

    :param abi_return: The ABI return value to decode
    :param method: The ABI method definition
    :raises ValueError: If there was an error decoding the return value
    :return: The decoded return value in ARC-56 format
    """
    return_type = method.returns.type
    if return_type == arc56.Void or abi_return.raw_value is None:
        return None
    assert isinstance(return_type, algokit_abi.ABIType)

    if abi_return.decode_error:
        raise ValueError(abi_return.decode_error)

    return return_type.decode(abi_return.raw_value)  # type: ignore[no-any-return]


def get_abi_encoded_value(value: object, abi_type: algokit_abi.ABIType | arc56.AVMType) -> bytes:
    """Encodes a value according to its ABI type.

    :param value: The value to encode
    :param abi_type: The ABI or AVM type
    :return: The ABI encoded bytes
    """
    if isinstance(value, (bytes | bytearray)):
        return bytes(value)
    if abi_type == arc56.AVMType.UINT64 and isinstance(value, int):
        return algokit_abi.ABIType.from_string("uint64").encode(value)
    if abi_type == arc56.AVMType.STRING and isinstance(value, str):
        return value.encode("utf-8")
    if abi_type == arc56.AVMType.BYTES and isinstance(value, bytes | bytearray):
        return bytes(value)
    assert not isinstance(abi_type, arc56.AVMType), "unexpected AVMType"
    return abi_type.encode(value)


def get_abi_decoded_value(
    value: bytes | int | str,
    decode_type: arc56.AVMType | algokit_abi.ABIType | arc56.ReferenceType,
) -> ABIValue:
    """Decodes a value according to its ABI type.

    :param value: The value to decode
    :param decode_type: The ABI type string or type object
    :return: The decoded ABI value
    """

    # map reference types to their value equivalents
    if decode_type in (arc56.ReferenceType.ASSET, arc56.ReferenceType.APPLICATION):
        decode_type = algokit_abi.UintType(64)
    elif decode_type == arc56.ReferenceType.ACCOUNT:
        decode_type = algokit_abi.AddressType()
    if decode_type == arc56.AVMType.UINT64:
        decode_type = algokit_abi.UintType(64)
    if decode_type == arc56.AVMType.BYTES or not isinstance(value, bytes):
        return value
    if decode_type == arc56.AVMType.STRING:
        return value.decode("utf-8")
    assert isinstance(decode_type, algokit_abi.ABIType), "unexpected ABIType"
    return decode_type.decode(value)  # type: ignore[no-any-return]


def prepare_value_for_atc(value: typing.Any, abi_type: algokit_abi.ABIType) -> typing.Any:  # noqa: ANN401
    """
    Recursively converts any structs present in value to a tuple,
    so it can be encoded by algosdk (which does not natively support structs)

    TODO: can remove this function once algosdk is removed from transact as algokit_abi supports struct natively
    """
    if isinstance(abi_type, algokit_abi.StructType):
        if isinstance(value, Mapping):
            result = []
            for key, field_type in abi_type.fields.items():
                if key not in value:
                    raise ValueError(f"Missing value for field '{key}'")
                value = prepare_value_for_atc(value[key], field_type)
                result.append(value)
            return result
        return [prepare_value_for_atc(v, t) for v, t in zip(value, abi_type.fields.values(), strict=True)]
    elif isinstance(abi_type, algokit_abi.TupleType):
        return [prepare_value_for_atc(v, t) for v, t in zip(value, abi_type.elements, strict=True)]
    elif isinstance(abi_type, algokit_abi.StaticArrayType | algokit_abi.DynamicArrayType):
        return [prepare_value_for_atc(v, abi_type.element) for v in value]
    else:
        return value


@dataclass(kw_only=True, frozen=True)
class BoxABIValue:
    """Represents an ABI value stored in a box."""

    name: BoxName
    """The name of the box"""
    value: ABIValue
    """The ABI value stored in the box"""
