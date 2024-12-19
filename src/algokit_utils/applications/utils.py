from typing import Any, TypeVar

from algosdk.abi import Method as AlgorandABIMethod
from algosdk.abi import TupleType

from algokit_utils.applications.app_spec.arc56 import (
    ABIArgumentType,
    ABITypeAlias,
    StructField,
)
from algokit_utils.applications.app_spec.arc56 import (
    Method as Arc56Method,
)
from algokit_utils.models.abi import ABIReturn, ABIStruct, ABIType, ABIValue

T = TypeVar("T", bound=ABIValue | bytes | ABIStruct | None)


def get_arc56_return_value(
    return_value: ABIReturn | None,
    method: Arc56Method | AlgorandABIMethod,
    structs: dict[str, list[StructField]],
) -> ABIValue | ABIStruct | None:
    """Checks for decode errors on the return value and maps it to the specified type.

    Args:
        return_value: The smart contract response
        method: The method that was called
        structs: The struct fields from the app spec

    Returns:
        The smart contract response with an updated return value

    Raises:
        ValueError: If there is a decode error
    """

    # Get method returns info
    if isinstance(method, AlgorandABIMethod):
        type_str = method.returns.type
        struct = None  # AlgorandABIMethod doesn't have struct info
    else:
        type_str = method.returns.type
        struct = method.returns.struct

    # Handle void/undefined returns
    if type_str == "void" or return_value is None:
        return None

    # Handle decode errors
    if return_value.decode_error:
        raise ValueError(return_value.decode_error)

    # Get raw return value
    raw_value = return_value.raw_value

    # Handle AVM types
    if type_str == "AVMBytes":
        return raw_value
    if type_str == "AVMString" and raw_value:
        return raw_value.decode("utf-8")
    if type_str == "AVMUint64" and raw_value:
        return ABIType.from_string("uint64").decode(raw_value)  # type: ignore[no-any-return]

    # Handle structs
    if struct and struct in structs:
        return_tuple = return_value.value
        return get_abi_struct_from_abi_tuple(return_tuple, structs[struct], structs)

    # Return as-is
    return return_value.value


def get_abi_encoded_value(value: Any, type_str: str, structs: dict[str, list[StructField]]) -> bytes:  # noqa: ANN401, PLR0911
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
    value: bytes | int | str, type_str: str | ABITypeAlias | ABIArgumentType, structs: dict[str, list[StructField]]
) -> ABIValue:
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
) -> TupleType:
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
    return TupleType(types)


def get_abi_struct_from_abi_tuple(
    decoded_tuple: Any,  # noqa: ANN401
    struct_fields: list[StructField],
    structs: dict[str, list[StructField]],
) -> dict[str, Any]:
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
