import dataclasses
import decimal

import pytest

import algokit_abi
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
    abi_type = algokit_abi.ABIType.from_string(abi_type_str)
    assert abi_type.byte_len() == expected_len


@pytest.mark.parametrize("bit_size", [i * 8 for i in range(1, 65)])
def test_uint_bit_sizes(bit_size: int) -> None:
    abi_type = algokit_abi.UintType(bit_size)
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
    abi_type = algokit_abi.UintType(bit_size=bit_size)
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
        algokit_abi.UintType(bit_size=bit_size)


@pytest.mark.parametrize(
    "bit_size",
    [
        8,
        64,
        512,
    ],
)
def test_uint_value_too_big(bit_size: int) -> None:
    abi_type = algokit_abi.UintType(bit_size=bit_size)
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
    abi_type = algokit_abi.UintType(bit_size=bit_size)
    with pytest.raises(OverflowError):
        abi_type.encode(-1)


@pytest.mark.parametrize("value", ["not an int", 1.23, decimal.Decimal("0.00"), b"\x00" * 8])
def test_uint_invalid_value_type(value: object) -> None:
    abi_type = algokit_abi.UintType(bit_size=64)
    with pytest.raises(TypeError):
        abi_type.encode(value)


@pytest.mark.parametrize(
    ("bit_size", "precision", "value_str", "expected_hex"),
    [
        (8, 1, "0.0", "00"),
        (8, 1, "0.1", "01"),
        (8, 1, "25.5", "FF"),
        (8, 2, "0.00", "00"),
        (8, 2, "0.01", "01"),
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
    abi_type = algokit_abi.UfixedType(bit_size=bit_size, precision=precision)
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    ("bit_size", "precision", "value", "expected_hex"),
    [
        (8, 30, 255, "FF"),
        (32, 10, 33, "00000021"),
    ],
)
def test_ufixed_int(bit_size: int, precision: int, value: int, expected_hex: str) -> None:
    abi_type = algokit_abi.UfixedType(bit_size=bit_size, precision=precision)
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
        algokit_abi.UfixedType(bit_size=bit_size, precision=1)


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
        algokit_abi.UfixedType(bit_size=512, precision=precision)


@pytest.mark.parametrize("value", ["not a decimal", 1.23, b"\x00" * 8])
def test_ufixed_invalid_value_type(value: object) -> None:
    abi_type = algokit_abi.UfixedType(64, 1)
    with pytest.raises(TypeError):
        abi_type.encode(value)


@pytest.mark.parametrize(
    "bit_size",
    [8, 64, 512],
)
def test_ufixed_value_too_big(bit_size: int) -> None:
    abi_type = algokit_abi.UfixedType(bit_size, 1)
    with pytest.raises(OverflowError):
        abi_type.encode(2**bit_size)


@pytest.mark.parametrize(
    "bit_size",
    [8, 64, 512],
)
def test_ufixed_value_negative(bit_size: int) -> None:
    abi_type = algokit_abi.UfixedType(bit_size, 1)
    with pytest.raises(OverflowError):
        abi_type.encode(-1)


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
    abi_type = algokit_abi.ByteType()
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


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
    abi_type = algokit_abi.ByteType()
    expected = bytes.fromhex(expected_hex)
    encoded = abi_type.encode(expected)
    assert encoded == expected, f"expected 0x{expected_hex} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        (False, "00"),
        (True, "80"),
    ],
)
def test_bool(*, value: bool, expected_hex: str) -> None:
    abi_type = algokit_abi.BoolType()
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


_ADDRESS = "MO2H6ZU47Q36GJ6GVHUKGEBEQINN7ZWVACMWZQGIYUOE3RBSRVYHV4ACJI"
_ADDRESS_BYTES = bytes.fromhex("63B47F669CFC37E327C6A9E8A31024821ADFE6D500996CC0C8C51C4DC4328D70")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(_ADDRESS, _ADDRESS_BYTES), (_ADDRESS_BYTES, _ADDRESS_BYTES), (ZERO_ADDRESS, b"\x00" * 32)],
)
def test_address(value: str | bytes, expected: bytes) -> None:
    abi_type = algokit_abi.AddressType()
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
    abi_type = algokit_abi.StringType()
    encoded = abi_type.encode(value)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be {expected!r}"


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
    abi_type = algokit_abi.StaticArrayType(element=algokit_abi.BoolType(), size=len(value))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        ([1, 2, 3], f"{1:016}{2:016}{3:016}"),
        ([_MAX_U64], "FF" * 8),
        ([_MAX_U64] * (_32K // 8), "FF" * _32K),
    ],
)
def test_uint64_static_array(value: list[int], expected_hex: str) -> None:
    abi_type = algokit_abi.StaticArrayType(element=algokit_abi.UintType(64), size=len(value))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    "element",
    [
        algokit_abi.UintType(64),
        algokit_abi.UfixedType(64, 2),
        algokit_abi.ByteType(),
        algokit_abi.BoolType(),
        algokit_abi.AddressType(),
    ],
)
def test_empty_array(element: algokit_abi.ABIType) -> None:
    abi_type = algokit_abi.DynamicArrayType(element)
    encoded = abi_type.encode([])
    assert encoded == b"\x00\x00", f"expected empty array of {element} to be 0x0000"


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
    abi_type = algokit_abi.DynamicArrayType(algokit_abi.BoolType())
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected bool array to be 0x{expected_hex}"


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        ([1, 2, 3], f"{3:04}{1:016}{2:016}{3:016}"),
        ([_MAX_U64], "0001" + "FF" * 8),
        ([_MAX_U64] * 2046, "07FE" + "FF" * (2046 * 8)),
    ],
)
def test_uint64_dynamic_array(value: list[int], expected_hex: str) -> None:
    abi_type = algokit_abi.DynamicArrayType(element=algokit_abi.UintType(64))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


@pytest.mark.parametrize(
    ("abi_type_name", "value", "expected_hex"),
    [
        ("(uint8,uint16)", (1, 2), "010002"),
        ("(uint32,uint32)", (1, 2), f"{1:08}{2:08}"),
        ("(uint32,string)", (42, "hello"), f"0000002A{6:04}" + b"\x00\x05hello".hex()),
        ("(uint16,bool)", (1234, False), "04D200"),
        ("(uint32,string,bool)", (42, "test", False), f"0000002A{7:04}00" + b"\x00\x04test".hex()),
        ("()", (), ""),
        ("(bool,bool,bool)", [False, True, True], "60"),
        ("(bool[3])", [[False, True, True]], "60"),
        ("(bool[])", [[False, True, True]], "0002000360"),
        ("(bool[2],bool[])", ([True, True], [True, True]), "C000030002C0"),
        ("(bool[],bool[])", [[], []], "0004000600000000"),
        ("(bool[],bool[])", [[True], [False]], "00040007000180000100"),
        ("(string,bool,bool,bool,bool,string)", ["AB", True, False, True, False, "DE"], "0005A000090002414200024445"),
        ("(uint16,(byte,address))", (42, (234, _ADDRESS)), "002AEA" + _ADDRESS_BYTES.hex()),
    ],
)
def test_tuples(abi_type_name: str, value: tuple, expected_hex: str) -> None:
    abi_type = algokit_abi.ABIType.from_string(abi_type_name)
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"


def _abi_metadata(abi_type_or_name: str | algokit_abi.ABIType) -> dict[str, object]:
    abi_type = (
        algokit_abi.ABIType.from_string(abi_type_or_name) if isinstance(abi_type_or_name, str) else abi_type_or_name
    )
    return {"abi": abi_type}


def _get_abi_type_from_dataclass(typ: type) -> algokit_abi.ABIType:
    fields = {f.name: _get_abi_type(f) for f in dataclasses.fields(typ)}
    return algokit_abi.StructType(fields=fields, decode_type=typ)


_TYPE_TO_DEFAULT_ABI = {
    int: "uint64",
    bool: "bool",
    bytes: "byte[]",
    str: "string",
}


def _get_abi_type(field: dataclasses.Field) -> algokit_abi.ABIType:
    if abi_type := field.metadata.get("abi"):
        return abi_type
    elif dataclasses.is_dataclass(field.type):
        return _get_abi_type_from_dataclass(field.type)
    else:
        abi_name = _TYPE_TO_DEFAULT_ABI.get(field.type)

    if abi_name is None:
        raise TypeError("could not determine abi type, use _abi_metadata")
    return algokit_abi.ABIType.from_string(abi_name)


@dataclasses.dataclass
class Foo:
    a: int = dataclasses.field(metadata=_abi_metadata("uint16"))
    b: str
    c: bytes


@dataclasses.dataclass
class Baz:
    a: int = dataclasses.field(metadata=_abi_metadata("uint8"))
    b: int = dataclasses.field(metadata=_abi_metadata("uint8"))


@dataclasses.dataclass
class Bar:
    a: bytes = dataclasses.field(metadata=_abi_metadata("byte"))
    b: list[Baz] = dataclasses.field(
        metadata=_abi_metadata(algokit_abi.StaticArrayType(_get_abi_type_from_dataclass(Baz), 3))
    )


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    [
        (
            Foo(7, "hello", b"world"),
            ("00070006000D" + b"\x00\x05hello\x00\x05world".hex()),
        ),
        (
            Bar(b"\x00", [Baz(1, 2), Baz(3, 4), Baz(5, 6)]),
            "00010203040506",
        ),
    ],
)
def test_struct(value: object, expected_hex: str) -> None:
    abi_type = _get_abi_type_from_dataclass(type(value))
    encoded = abi_type.encode(value)
    expected = bytes.fromhex(expected_hex)
    assert encoded == expected, f"expected {value} encoded as {abi_type} to be 0x{expected_hex}"
    decoded = abi_type.decode(expected)
    assert value == decoded, "expected decoded to match"
