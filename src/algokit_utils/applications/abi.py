from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias

import algosdk
from algosdk.abi.method import Method as AlgorandABIMethod
from algosdk.atomic_transaction_composer import ABIResult

from algokit_utils.applications.app_spec.arc56 import Arc56Contract, StructField
from algokit_utils.applications.app_spec.arc56 import Method as Arc56Method

if TYPE_CHECKING:
    from algokit_utils.models.state import BoxName

ABIValue: TypeAlias = (
    bool | int | str | bytes | bytearray | list["ABIValue"] | tuple["ABIValue"] | dict[str, "ABIValue"]
)
ABIStruct: TypeAlias = dict[str, list[dict[str, "ABIValue"]]]
Arc56ReturnValueType: TypeAlias = ABIValue | ABIStruct | None


ABIType: TypeAlias = algosdk.abi.ABIType
ABIArgumentType: TypeAlias = algosdk.abi.ABIType | algosdk.abi.ABITransactionType | algosdk.abi.ABIReferenceType

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
    "get_abi_struct_from_abi_tuple",
    "get_abi_tuple_from_abi_struct",
    "get_abi_tuple_type_from_abi_struct_definition",
    "get_arc56_value",
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
    method: AlgorandABIMethod | None = None
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

    def get_arc56_value(
        self, method: Arc56Method | AlgorandABIMethod, structs: dict[str, list[StructField]]
    ) -> Arc56ReturnValueType:
        """Gets the ARC-56 formatted return value.

        :param method: The ABI method definition
        :param structs: Dictionary of struct definitions
        :return: The decoded return value in ARC-56 format
        """
        return get_arc56_value(self, method, structs)


def get_arc56_value(
    abi_return: ABIReturn, method: Arc56Method | AlgorandABIMethod, structs: dict[str, list[StructField]]
) -> Arc56ReturnValueType:
    """Gets the ARC-56 formatted return value from an ABI return.

    :param abi_return: The ABI return value to decode
    :param method: The ABI method definition
    :param structs: Dictionary of struct definitions
    :raises ValueError: If there was an error decoding the return value
    :return: The decoded return value in ARC-56 format
    """
    if isinstance(method, AlgorandABIMethod):
        type_str = method.returns.type
        struct = None  # AlgorandABIMethod doesn't have struct info
    else:
        type_str = method.returns.type
        struct = method.returns.struct

    if type_str == "void" or abi_return.value is None:
        return None

    if abi_return.decode_error:
        raise ValueError(abi_return.decode_error)

    raw_value = abi_return.raw_value

    # Handle AVM types
    if type_str == "AVMBytes":
        return raw_value
    if type_str == "AVMString" and raw_value:
        return raw_value.decode("utf-8")
    if type_str == "AVMUint64" and raw_value:
        return ABIType.from_string("uint64").decode(raw_value)  # type: ignore[no-any-return]

    # Handle structs
    if struct and struct in structs:
        return_tuple = abi_return.value
        return Arc56Contract.get_abi_struct_from_abi_tuple(return_tuple, structs[struct], structs)

    # Return as-is
    return abi_return.value


def get_abi_encoded_value(value: Any, type_str: str, structs: dict[str, list[StructField]]) -> bytes:  # noqa: PLR0911, ANN401
    """Encodes a value according to its ABI type.

    :param value: The value to encode
    :param type_str: The ABI type string
    :param structs: Dictionary of struct definitions
    :raises ValueError: If the value cannot be encoded for the given type
    :return: The ABI encoded bytes
    """
    if isinstance(value, (bytes | bytearray)):
        return value
    if type_str == "AVMUint64":
        return ABIType.from_string("uint64").encode(value)
    if type_str in ("AVMBytes", "AVMString"):
        if isinstance(value, str):
            return value.encode("utf-8")
        if not isinstance(value, (bytes | bytearray)):
            raise ValueError(f"Expected bytes value for {type_str}, but got {type(value)}")
        return value
    if type_str in structs:
        tuple_type = get_abi_tuple_type_from_abi_struct_definition(structs[type_str], structs)
        if isinstance(value, (list | tuple)):
            return tuple_type.encode(value)  # type: ignore[arg-type]
        else:
            tuple_values = get_abi_tuple_from_abi_struct(value, structs[type_str], structs)
            return tuple_type.encode(tuple_values)
    else:
        abi_type = ABIType.from_string(type_str)
        return abi_type.encode(value)


def get_abi_decoded_value(
    value: bytes | int | str, type_str: str | ABIArgumentType, structs: dict[str, list[StructField]]
) -> ABIValue:
    """Decodes a value according to its ABI type.

    :param value: The value to decode
    :param type_str: The ABI type string or type object
    :param structs: Dictionary of struct definitions
    :return: The decoded ABI value
    """
    type_value = str(type_str)

    if type_value == "AVMBytes" or not isinstance(value, bytes):
        return value
    if type_value == "AVMString":
        return value.decode("utf-8")
    if type_value == "AVMUint64":
        return ABIType.from_string("uint64").decode(value)  # type: ignore[no-any-return]
    if type_value in structs:
        tuple_type = get_abi_tuple_type_from_abi_struct_definition(structs[type_value], structs)
        decoded_tuple = tuple_type.decode(value)
        return get_abi_struct_from_abi_tuple(decoded_tuple, structs[type_value], structs)
    return ABIType.from_string(type_value).decode(value)  # type: ignore[no-any-return]


def get_abi_tuple_from_abi_struct(
    struct_value: dict[str, Any],
    struct_fields: list[StructField],
    structs: dict[str, list[StructField]],
) -> list[Any]:
    """Converts an ABI struct to a tuple representation.

    :param struct_value: The struct value as a dictionary
    :param struct_fields: List of struct field definitions
    :param structs: Dictionary of struct definitions
    :raises ValueError: If a required field is missing from the struct
    :return: The struct as a tuple
    """
    result = []
    for field in struct_fields:
        key = field.name
        if key not in struct_value:
            raise ValueError(f"Missing value for field '{key}'")
        value = struct_value[key]
        field_type = field.type
        if isinstance(field_type, str):
            if field_type in structs:
                value = get_abi_tuple_from_abi_struct(value, structs[field_type], structs)
        elif isinstance(field_type, list):
            value = get_abi_tuple_from_abi_struct(value, field_type, structs)
        result.append(value)
    return result


def get_abi_tuple_type_from_abi_struct_definition(
    struct_def: list[StructField], structs: dict[str, list[StructField]]
) -> algosdk.abi.TupleType:
    """Creates a TupleType from a struct definition.

    :param struct_def: The struct field definitions
    :param structs: Dictionary of struct definitions
    :raises ValueError: If a field type is invalid
    :return: The TupleType representing the struct
    """
    types = []
    for field in struct_def:
        field_type = field.type
        if isinstance(field_type, str):
            if field_type in structs:
                types.append(get_abi_tuple_type_from_abi_struct_definition(structs[field_type], structs))
            else:
                types.append(ABIType.from_string(field_type))  # type: ignore[arg-type]
        elif isinstance(field_type, list):
            types.append(get_abi_tuple_type_from_abi_struct_definition(field_type, structs))
        else:
            raise ValueError(f"Invalid field type: {field_type}")
    return algosdk.abi.TupleType(types)


def get_abi_struct_from_abi_tuple(
    decoded_tuple: Any,  # noqa: ANN401
    struct_fields: list[StructField],
    structs: dict[str, list[StructField]],
) -> dict[str, Any]:
    """Converts a decoded tuple to an ABI struct.

    :param decoded_tuple: The tuple to convert
    :param struct_fields: List of struct field definitions
    :param structs: Dictionary of struct definitions
    :return: The tuple as a struct dictionary
    """
    result = {}
    for i, field in enumerate(struct_fields):
        key = field.name
        field_type = field.type
        value = decoded_tuple[i]
        if isinstance(field_type, str):
            if field_type in structs:
                value = get_abi_struct_from_abi_tuple(value, structs[field_type], structs)
        elif isinstance(field_type, list):
            value = get_abi_struct_from_abi_tuple(value, field_type, structs)
        result[key] = value
    return result


@dataclass(kw_only=True, frozen=True)
class BoxABIValue:
    """Represents an ABI value stored in a box."""

    name: BoxName
    """The name of the box"""
    value: ABIValue
    """The ABI value stored in the box"""
