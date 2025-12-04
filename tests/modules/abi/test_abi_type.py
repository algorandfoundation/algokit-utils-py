import dataclasses
import decimal

import pytest

from algokit_abi import abi
from algokit_common.constants import ZERO_ADDRESS

_32K = 32 * 1024
_MAX_U16 = 2**16 - 1
_MAX_U32 = 2**32 - 1
_MAX_U64 = 2**64 - 1


@pytest.mark.parametrize(
    ("abi_type_str", "expected_len"),
    [
        ("bool", 1),
        ("bool[2]", 1),
        ("bool[8]", 1),
        ("bool[9]", 2),
    ],
)
def test_byte_len(abi_type_str: str, expected_len: int) -> None:
    abi_type = abi.ABIType.from_string(abi_type_str)
    assert abi_type.byte_len() == expected_len


@pytest.mark.parametrize("bit_size", [i * 8 for i in range(1, 65)])
def test_uint_bit_sizes(bit_size: int) -> None:
    abi_type = abi.UintType(bit_size)
    assert abi_type.bit_size == bit_size


@pytest.mark.parametrize(
    ("bit_size", "value", "expected_hex"),
    [
        (8, 0, "00"),
        (8, 1, "01"),
        (8, 15, "0F"),
        (8, 16, "10"),
        (8, 254, "FE"),
        (8, 255, "FF"),
        (16, 0, "0000"),
        (16, 1, "0001"),
        (16, 3, "0003"),
        (16, _MAX_U16, "FFFF"),
        (32, 0, "00000000"),
        (32, 1, "00000001"),
        (32, _MAX_U32, "FFFFFFFF"),
        (64, 0, "0000000000000000"),
        (64, 1, "0000000000000001"),
        (64, 256, "0000000000000100"),
        (64, _MAX_U64, "FFFFFFFFFFFFFFFF"),
        (128, 0, "00" * 16),
        (128, 1, "00" * 15 + "01"),
        (128, 2**128 - 1, "FF" * 16),
        (256, 0, "00" * 32),
        (256, 1, "00" * 31 + "01"),
        (256, 2**256 - 1, "FF" * 32),
        (512, 0, "00" * 64),
        (512, 1, "00" * 63 + "01"),
        (512, 2**512 - 1, "FF" * 64),
    ],
)
def test_uint(bit_size: int, value: int, expected_hex: str) -> None:
    abi_type = abi.UintType(bit_size=bit_size)
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    "bit_size",
    [
        -512,
        -8,
        -1,
        0,
        1,
        7,
        9,
        15,
        23,
        25,
        520,
    ],
)
def test_uint_invalid_size(bit_size: int) -> None:
    with pytest.raises(ValueError, match="bit_size must be between 8 and 512"):
        abi.UintType(bit_size=bit_size)


@pytest.mark.parametrize(
    "bit_size",
    [
        8,
        64,
        512,
    ],
)
def test_uint_value_too_big(bit_size: int) -> None:
    abi_type = abi.UintType(bit_size=bit_size)
    with pytest.raises(OverflowError):
        abi_type.encode(2**bit_size)


@pytest.mark.parametrize(
    "bit_size",
    [
        8,
        64,
        512,
    ],
)
def test_uint_value_negative(bit_size: int) -> None:
    abi_type = abi.UintType(bit_size=bit_size)
    with pytest.raises(OverflowError):
        abi_type.encode(-1)


@pytest.mark.parametrize("value", ["not an int", 1.23, decimal.Decimal("0.00"), b"\x00" * 8])
def test_uint_invalid_value_type(value: object) -> None:
    abi_type: abi.ABIType = abi.UintType(bit_size=64)
    with pytest.raises(TypeError):
        abi_type.encode(value)


@pytest.mark.parametrize(
    ("bit_size", "precision", "value_str", "expected_hex"),
    [
        (8, 1, "0.0", "00"),
        (8, 1, "0.1", "01"),
        (8, 1, "25.5", "FF"),
        (8, 2, ".01", "01"),
        (8, 2, "0.01", "01"),
        (8, 2, ".1", "0A"),
        (8, 2, "0.1", "0A"),
        (8, 2, "1.000", "64"),
        (8, 2, "0.00", "00"),
        (8, 2, "0.00000", "00"),
        (8, 2, "2.55", "FF"),
        (16, 1, "0.0", "0000"),
        (16, 1, "0.1", "0001"),
        (16, 1, "6553.5", "FFFF"),
        (512, 160, "0." + "0" * 160, "00" * 64),
        (512, 160, "0." + "0" * 159 + "1", "00" * 63 + "01"),
    ],
)
def test_ufixed_decimal(bit_size: int, precision: int, value_str: str, expected_hex: str) -> None:
    value = decimal.Decimal(value_str)
    abi_type = abi.UfixedType(bit_size=bit_size, precision=precision)
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    ("bit_size", "precision", "value", "expected_hex"),
    [
        (8, 2, 0, "00"),
        (8, 2, 1, "01"),
        (8, 30, 255, "FF"),
        (32, 10, 33, "00000021"),
    ],
)
def test_ufixed_int(bit_size: int, precision: int, value: int, expected_hex: str) -> None:
    abi_type = abi.UfixedType(bit_size=bit_size, precision=precision)
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    "bit_size",
    [
        -512,
        -8,
        -1,
        0,
        1,
        7,
        9,
        15,
        23,
        25,
        520,
    ],
)
def test_ufixed_invalid_size(bit_size: int) -> None:
    with pytest.raises(ValueError, match="bit_size must be between 8 and 512"):
        abi.UfixedType(bit_size=bit_size, precision=1)


@pytest.mark.parametrize(
    "precision",
    [
        -1,
        0,
        161,
    ],
)
def test_ufixed_invalid_precision(precision: int) -> None:
    with pytest.raises(ValueError, match="precision must be between 0 and 160"):
        abi.UfixedType(bit_size=512, precision=precision)


@pytest.mark.parametrize("value", ["not a decimal", 1.23, b"\x00" * 8])
def test_ufixed_invalid_value_type(value: object) -> None:
    abi_type: abi.ABIType = abi.UfixedType(64, 1)
    with pytest.raises(TypeError):
        abi_type.encode(value)


@pytest.mark.parametrize(
    "bit_size",
    [8, 64, 512],
)
def test_ufixed_value_too_big(bit_size: int) -> None:
    abi_type = abi.UfixedType(bit_size, 1)
    with pytest.raises(OverflowError):
        abi_type.encode(2**bit_size)


@pytest.mark.parametrize(
    "bit_size",
    [8, 64, 512],
)
def test_ufixed_value_negative(bit_size: int) -> None:
    abi_type = abi.UfixedType(bit_size, 1)
    with pytest.raises(OverflowError):
        abi_type.encode(-1)


def test_ufixed_value_too_precise() -> None:
    abi_type = abi.UfixedType(8, 1)
    with pytest.raises(ValueError, match="precision exceeds 1"):
        abi_type.encode(decimal.Decimal("1.001"))


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        (0, "00"),
        (1, "01"),
        (10, "0A"),
        (254, "FE"),
        (255, "FF"),
    ],
)
def test_byte_int(value: int, expected_hex: str) -> None:
    abi_type = abi.ByteType()
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == bytes.fromhex(expected_hex)


@pytest.mark.parametrize(
    "expected_hex",
    [
        "00",
        "01",
        "0A",
        "80",
        "FE",
        "FF",
    ],
)
def test_byte_byte(expected_hex: str) -> None:
    abi_type = abi.ByteType()
    expected = bytes.fromhex(expected_hex)
    encoded = abi_type.encode(expected)
    assert encoded == expected, f"expected 0x{expected_hex} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == expected, f"expected decoded value {decoded} to equal original value {expected}"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        (False, "00"),
        (True, "80"),
    ],
)
def test_bool(*, value: bool, expected_hex: str) -> None:
    abi_type = abi.BoolType()
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


_ADDRESS = "MO2H6ZU47Q36GJ6GVHUKGEBEQINN7ZWVACMWZQGIYUOE3RBSRVYHV4ACJI"
_ADDRESS_BYTES = bytes.fromhex("63B47F669CFC37E327C6A9E8A31024821ADFE6D500996CC0C8C51C4DC4328D70")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(_ADDRESS, _ADDRESS_BYTES), (_ADDRESS_BYTES, _ADDRESS_BYTES), (ZERO_ADDRESS, b"\x00" * 32)],
)
def test_address(value: str | bytes, expected: bytes) -> None:
    abi_type = abi.AddressType()
    encoded = abi_type.encode(value)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected.hex()}"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("What's new", b"\x00\x0aWhat's new"),
        (
            "😅🔨",
            bytes([0, 8, 240, 159, 152, 133, 240, 159, 148, 168]),
        ),
        ("asdf", b"\x00\x04asdf"),
    ],
)
def test_string(value: str, expected: bytes) -> None:
    abi_type = abi.StringType()
    encoded = abi_type.encode(value)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be {expected!r}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        ([True], "80"),
        ([False], "00"),
        ([True, True, False], "C0"),
        ([False, True, False, False, False, False, False, False], "40"),
        ([True] * 8, "FF"),
        ([True, False, False, True, False, False, True, False, True], "9280"),
        ([True] * (_32K * 8), "FF" * _32K),  # biggest bool static array that can be stored in a box
    ],
)
def test_bool_static_array(value: list[bool], expected_hex: str) -> None:
    abi_type = abi.StaticArrayType(element=abi.BoolType(), size=len(value))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        ([1, 2, 3], f"{1:016}{2:016}{3:016}"),
        ([_MAX_U64], "FF" * 8),
        ([_MAX_U64] * (_32K // 8), "FF" * _32K),
    ],
)
def test_uint64_static_array(value: list[int], expected_hex: str) -> None:
    abi_type = abi.StaticArrayType(element=abi.UintType(64), size=len(value))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


@pytest.mark.parametrize(
    "element",
    [
        abi.UintType(64),
        abi.UfixedType(64, 2),
        abi.ByteType(),
        abi.BoolType(),
        abi.AddressType(),
    ],
)
def test_empty_array(element: abi.ABIType) -> None:
    abi_type = abi.DynamicArrayType(element)
    encoded = abi_type.encode([])
    assert encoded == b"\x00\x00", f"expected empty array of {element} to be 0x0000"
    decoded = abi_type.decode(encoded)
    assert not decoded, "expected decoded empty array to be empty"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        ([True, True, False], "0003C0"),
        ([True] * 8, "0008FF"),
        ([True, False, False, True, False, False, True, False, True], "00099280"),
        ([False] * _MAX_U16, "FFFF" + "00" * 8192),
        ([True] * _MAX_U16, "FF" * 8193 + "FE"),
    ],
)
def test_bool_dynamic_array(value: list[bool], expected_hex: str) -> None:
    abi_type = abi.DynamicArrayType(abi.BoolType())
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected bool array to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        ([1, 2, 3], f"{3:04}{1:016}{2:016}{3:016}"),
        ([_MAX_U64], "0001" + "FF" * 8),
        ([_MAX_U64] * 2046, "07FE" + "FF" * (2046 * 8)),
    ],
)
def test_uint64_dynamic_array(value: list[int], expected_hex: str) -> None:
    abi_type = abi.DynamicArrayType(element=abi.UintType(64))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


@pytest.mark.parametrize(
    ("abi_type_name", "value", "expected_hex"),
    [
        ("(uint8,uint16)", (1, 2), "010002"),
        ("(uint32,uint32)", (1, 2), f"{1:08}{2:08}"),
        ("(uint32,string)", (42, "hello"), f"0000002A{6:04}" + b"\x00\x05hello".hex()),
        ("(uint16,bool)", (1234, False), "04D200"),
        ("(uint32,string,bool)", (42, "test", False), f"0000002A{7:04}00" + b"\x00\x04test".hex()),
        ("()", (), ""),
        ("(bool,bool,bool)", (False, True, True), "60"),
        ("(bool[3])", ([False, True, True],), "60"),
        ("(bool[])", ([False, True, True],), "0002000360"),
        ("(bool[2],bool[])", ([True, True], [True, True]), "C000030002C0"),
        ("(bool[],bool[])", ([], []), "0004000600000000"),
        ("(bool[],bool[])", ([True], [False]), "00040007000180000100"),
        ("(string,bool,bool,bool,bool,string)", ("AB", True, False, True, False, "DE"), "0005A000090002414200024445"),
        ("(uint16,(byte,address))", (42, (b"\xea", _ADDRESS)), "002AEA" + _ADDRESS_BYTES.hex()),
        ("(string,uint32)", ("test", 7), f"0006{7:08}" + b"\x00\x04test".hex()),
    ],
)
def test_tuples(abi_type_name: str, value: tuple, expected_hex: str) -> None:
    abi_type = abi.ABIType.from_string(abi_type_name)
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


def _abi_meta(abi_type_or_name: str | abi.ABIType) -> dict[str, object]:
    abi_type = abi.ABIType.from_string(abi_type_or_name) if isinstance(abi_type_or_name, str) else abi_type_or_name
    return {"abi": abi_type}


def _dataclass_to_abi_type(typ: type) -> abi.ABIType:
    fields = {f.name: _get_abi_type(f) for f in dataclasses.fields(typ)}
    return abi.StructType(struct_name=typ.__name__, fields=fields, decode_type=typ)


_TYPE_TO_DEFAULT_ABI = {
    int: "uint64",
    bool: "bool",
    bytes: "byte[]",
    str: "string",
}


def _get_abi_type(field: dataclasses.Field) -> abi.ABIType:
    if abi_type := field.metadata.get("abi"):
        return abi_type
    elif dataclasses.is_dataclass(field.type):
        return _dataclass_to_abi_type(field.type)
    else:
        abi_name = _TYPE_TO_DEFAULT_ABI.get(field.type)

    if abi_name is None:
        raise TypeError("could not determine abi type, use _abi_metadata")
    return abi.ABIType.from_string(abi_name)


@dataclasses.dataclass
class Foo:
    a: int = dataclasses.field(metadata=_abi_meta("uint16"))
    b: str
    c: bytes


@dataclasses.dataclass
class Baz:
    a: int = dataclasses.field(metadata=_abi_meta("uint8"))
    b: int = dataclasses.field(metadata=_abi_meta("uint16"))


_BAZ_ABI_TYPE = _dataclass_to_abi_type(Baz)


@dataclasses.dataclass
class Bar:
    a: bytes = dataclasses.field(metadata=_abi_meta("byte"))
    b: list[Baz] = dataclasses.field(metadata=_abi_meta(abi.StaticArrayType(_dataclass_to_abi_type(Baz), 3)))


@dataclasses.dataclass
class Large:
    many_bar: list[Bar] = dataclasses.field(metadata=_abi_meta(abi.DynamicArrayType(_dataclass_to_abi_type(Bar))))
    large_bytes: bytes = dataclasses.field(metadata=_abi_meta("byte[1024]"))


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        (
            Foo(7, "hello", b"world"),
            ("00070006000D" + b"\x00\x05hello\x00\x05world".hex()),
        ),
        (
            Bar(b"\x00", [Baz(1, 2), Baz(3, 4), Baz(5, 6)]),
            "00010002030004050006",
        ),
        (
            Large(
                many_bar=[
                    Bar(b"\x00", [Baz(1, 2), Baz(3, 4), Baz(5, 6)]),
                    Bar(b"\x07", [Baz(8, 9), Baz(10, 11), Baz(12, 13)]),
                ],
                large_bytes=b"A" * 1024,
            ),
            "0402" + b"A".hex() * 1024 + "000200010002030004050006070800090A000B0C000D",
        ),
    ],
)
def test_struct(value: object, expected_hex: str) -> None:
    abi_type = _dataclass_to_abi_type(type(value))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(encoded)
    assert decoded == value, f"expected decoded value {decoded} to equal original value {value}"


def test_struct_equality() -> None:
    fields = {"foo": abi.ByteType(), "bar": abi.BoolType()}
    struct = abi.StructType(struct_name="A", fields=fields)

    same_name_and_field = abi.StructType(struct_name="A", fields=fields)
    assert struct == same_name_and_field, "structs with the same name and fields should be equal"

    same_fields_different_name = abi.StructType(struct_name="B", fields=fields)
    assert struct != same_fields_different_name, "structs with different name and same fields should not be equal"

    same_name_different_fields = abi.StructType(struct_name="A", fields={"foo": abi.ByteType()})
    assert struct != same_name_different_fields, "structs with same name and different fields should not be equal"


@pytest.mark.parametrize(
    "abi_type_str",
    [
        "byte[",
        "(byte",
        "bad",
        "(byte))",
        "uintbad",
        "ufixedbad",
        "ufixedbadx2",
        "ufixed2xbad",
        "uint64[bad]",
        "ufixedbadx2x3",
        "ufixed2x3x4",
        "ufixedbad2x3[]",
        "(uint64,bad)",
    ],
)
def test_from_string_errors(abi_type_str: str) -> None:
    with pytest.raises(ValueError, match="unknown abi type"):
        abi.ABIType.from_string(abi_type_str)


def test_missing_tup_element() -> None:
    with pytest.raises(ValueError, match="commas must follow a tuple element"):
        abi.ABIType.from_string("(byte,,byte)")


def test_trailing_comma() -> None:
    with pytest.raises(ValueError, match="cannot have leading or trailing commas"):
        abi.ABIType.from_string("(byte,)")
