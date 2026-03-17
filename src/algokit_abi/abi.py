import abc
import dataclasses
import decimal
import typing
from collections.abc import Iterator, Mapping, Sequence
from functools import cached_property

from algokit_common import address_from_public_key, public_key_from_address

BytesLike = bytes | bytearray | memoryview


_ABI_BOOL_TRUE_UINT = 0x80
_ABI_BOOL_TRUE = _ABI_BOOL_TRUE_UINT.to_bytes(length=1, byteorder="big")
_ABI_BOOL_FALSE = b"\x00"
_MAX_UINT_N = 512
_U16_NUM_BYTES = 2
_MAX_U16 = 2**16 - 1


class ABIType(abc.ABC):
    @property
    def display_name(self) -> str:
        return self.name

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def encode(self, value: typing.Any) -> bytes: ...  # noqa: ANN401

    @abc.abstractmethod
    def decode(self, value: BytesLike) -> typing.Any: ...  # noqa: ANN401

    def is_dynamic(self) -> bool:
        return self.byte_len() is None

    @abc.abstractmethod
    def byte_len(self) -> int | None: ...

    @classmethod
    def from_string(cls, value: str) -> "ABIType":
        try:
            return _COMMON_TYPES[value]
        except KeyError:
            pass
        if value.startswith("(") and value.endswith(")"):
            tup_inner = value[1:-1]
            tup_elements = [cls.from_string(t) for t in split_tuple_str(tup_inner)]
            return TupleType(tup_elements)
        if value.endswith("[]"):
            element = cls.from_string(value[:-2])
            return DynamicArrayType(element)
        if value.endswith("]"):
            array_start = value.rindex("[")
            size_str = value[array_start + 1 : -1]
            try:
                size = int(size_str)
            except ValueError:
                pass  # fall through to error
            else:
                element = cls.from_string(value[:array_start])
                return StaticArrayType(element, size)
        elif value.startswith("ufixed"):
            n_m_str = value.removeprefix("ufixed")
            try:
                n, m = map(int, n_m_str.split("x"))
            except ValueError:
                pass  # fall through to error
            else:
                return UfixedType(n, m)
        raise ValueError(f"unknown abi type: {value}")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StructType):
            # structs can only equal structs
            return False
        if isinstance(other, ABIType):
            return self.name == other.name
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.display_name)

    def __str__(self) -> str:
        return self.display_name

    def _check_num_bytes(self, value: BytesLike) -> None:
        expected_bytes_len = self.byte_len()
        if expected_bytes_len is not None and len(value) != expected_bytes_len:
            raise ValueError(f"expected {expected_bytes_len} bytes for {self.display_name}, got {len(value)} bytes")


@typing.final
class BoolType(ABIType):
    @property
    def name(self) -> str:
        return "bool"

    def byte_len(self) -> int:
        return 1

    def encode(self, value: bool) -> bytes:  # noqa: FBT001
        # note: bool in an array or tuple is handled separately
        # intentionally comparing to True and False to handle invalid types
        if value is True:
            return _ABI_BOOL_TRUE
        elif value is False:
            return _ABI_BOOL_FALSE
        else:
            raise ValueError(f"expected a bool, got: {_error_str(value)}")

    def decode(self, value: BytesLike) -> bool:
        if value == _ABI_BOOL_TRUE:
            return True
        elif value == _ABI_BOOL_FALSE:
            return False
        else:
            raise ValueError(f"bool value could not be decoded: {_error_str(value)}")


@typing.final
@dataclasses.dataclass(frozen=True)
class UintType(ABIType):
    bit_size: int = dataclasses.field()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.bit_size, int)
            or self.bit_size <= 0
            or self.bit_size > _MAX_UINT_N
            or self.bit_size % 8 != 0
        ):
            raise ValueError(f"bit_size must be between 8 and {_MAX_UINT_N} and divisible by 8")

    @property
    def name(self) -> str:
        return f"uint{self.bit_size}"

    def byte_len(self) -> int:
        return self.bit_size // 8

    def encode(self, value: int) -> bytes:
        if not isinstance(value, int):
            raise TypeError("expected int")
        return value.to_bytes(self.byte_len(), byteorder="big", signed=False)

    def decode(self, value: BytesLike) -> int:
        self._check_num_bytes(value)
        return int.from_bytes(value, byteorder="big", signed=False)


_MAX_PRECISION = 160


@typing.final
@dataclasses.dataclass(frozen=True)
class UfixedType(ABIType):
    bit_size: int
    precision: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.bit_size, int)
            or self.bit_size <= 0
            or self.bit_size > _MAX_UINT_N
            or self.bit_size % 8 != 0
        ):
            raise ValueError(f"bit_size must be between 8 and {_MAX_UINT_N} and divisible by 8")
        if not isinstance(self.precision, int) or self.precision <= 0 or self.precision > _MAX_PRECISION:
            raise ValueError(f"precision must be between 0 and {_MAX_PRECISION}")

    @property
    def name(self) -> str:
        return f"ufixed{self.bit_size}x{self.precision}"

    def byte_len(self) -> int:
        return self._int_type.byte_len()

    @cached_property
    def _int_type(self) -> UintType:
        return UintType(bit_size=self.bit_size)

    def encode(self, value: decimal.Decimal | int) -> bytes:
        if isinstance(value, decimal.Decimal):
            value = value.normalize()
            decimal_tuple = value.as_tuple()
            exponent = decimal_tuple.exponent
            if not isinstance(exponent, int):
                raise ValueError(f"unsupported decimal: {_error_str(value)}")
            if -exponent > self.precision:
                raise ValueError(f"precision exceeds {self.precision}: {_error_str(value)}")
            value_int = int(value * 10**self.precision)
        else:
            value_int = value
        return self._int_type.encode(value_int)

    def decode(self, value: BytesLike) -> decimal.Decimal:
        int_value = self._int_type.decode(value)
        int_str = str(int_value).zfill(self.precision)
        decimal_str = int_str[: -self.precision] + "." + int_str[-self.precision :]
        return decimal.Decimal(decimal_str)


@typing.final
@dataclasses.dataclass(frozen=True)
class ByteType(ABIType):
    _uint_type: UintType = dataclasses.field(default=UintType(bit_size=8), init=False)

    @property
    def name(self) -> str:
        return "byte"

    def byte_len(self) -> int:
        return self._uint_type.byte_len()

    def encode(self, value: int | bytes | bytearray) -> bytes:
        if isinstance(value, int):
            return self._uint_type.encode(value)
        elif len(value) == 1:
            return bytes(value)
        else:
            raise ValueError(f"expected 1 byte: {_error_str(value)}")

    def decode(self, value: BytesLike) -> bytes:
        self._check_num_bytes(value)
        return bytes(value)


@dataclasses.dataclass(frozen=True)
class DynamicArrayType(ABIType):
    element: ABIType

    @property
    def display_name(self) -> str:
        return f"{self.element.display_name}[]"

    @property
    def name(self) -> str:
        return f"{self.element.name}[]"

    def byte_len(self) -> None:
        return None

    def encode(self, value: Sequence | bytes | bytearray) -> bytes:
        static_type = StaticArrayType(element=self.element, size=len(value))
        try:
            len_bytes = _int_to_u16_bytes(len(value))
        except OverflowError:
            raise ValueError(f"array length exceeds {_MAX_U16}") from None
        return len_bytes + static_type.encode(value)

    def decode(self, value: BytesLike) -> list | bytes:
        data = memoryview(value)
        if data.nbytes < _U16_NUM_BYTES:
            raise ValueError(f"not enough bytes to decode {self}: {_error_str(value)}")

        array_len = int.from_bytes(data[:_U16_NUM_BYTES], byteorder="big")

        static_type = StaticArrayType(element=self.element, size=array_len)
        return static_type.decode(data[_U16_NUM_BYTES:])


@dataclasses.dataclass(frozen=True)
class _RepeatedSequence(Sequence[ABIType]):
    element: ABIType
    size: int

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[ABIType]:
        for _ in range(self.size):
            yield self.element

    def __getitem__(self, item: int) -> ABIType:  # type: ignore[override]
        if item >= self.size or -item > self.size:
            raise IndexError("index out of range")
        return self.element

    def __contains__(self, x: object, /) -> bool:
        return x == self.element


@typing.final
@dataclasses.dataclass(frozen=True)
class StaticArrayType(ABIType):
    element: ABIType
    size: int

    @property
    def display_name(self) -> str:
        return f"{self.element.display_name}[{self.size}]"

    @property
    def name(self) -> str:
        return f"{self.element.name}[{self.size}]"

    @cached_property
    def _tuple_type(self) -> "TupleType":
        return TupleType(elements=_RepeatedSequence(self.element, self.size))

    def byte_len(self) -> int | None:
        return self._tuple_type.byte_len()

    def encode(self, value: Sequence | bytes | bytearray) -> bytes:
        return self._tuple_type.encode(value)

    def decode(self, value: BytesLike) -> list | bytes:
        result = self._tuple_type.decode(value)
        if isinstance(result, bytes):
            return result
        else:
            return list(result)


@typing.final
@dataclasses.dataclass(frozen=True)
class TupleType(ABIType):
    elements: Sequence[ABIType]

    @cached_property
    def display_name(self) -> str:
        if self._homogenous_element:
            return f"{self._homogenous_element.display_name}[{len(self.elements)}]"
        else:
            return f"({','.join(v.display_name for v in self.elements)})"

    @cached_property
    def name(self) -> str:
        return f"({','.join(v.name for v in self.elements)})"

    def byte_len(self) -> int | None:
        return self._byte_len

    @cached_property
    def _byte_len(self) -> int | None:
        total_bits = 0
        for el in self.elements:
            if el.name == "bool":
                total_bits += 1
            else:
                el_byte_len = el.byte_len()
                if el_byte_len is None:
                    return None
                total_bits = _round_bits_to_nearest_byte(total_bits) + el_byte_len * 8
            if self._homogenous_element:
                total_bits *= len(self.elements)
                break
        return _bits_to_byte(total_bits)

    @cached_property
    def _homogenous_element(self) -> ABIType | None:
        if isinstance(self.elements, _RepeatedSequence):
            return self.elements.element
        elif len({e.name for e in self.elements}) == 1:
            return next(iter(self.elements))
        else:
            return None

    @cached_property
    def _head_num_bytes(self) -> int:
        num_bits = 0
        for element in self.elements:
            if _is_bool(element):
                num_bits += 1
            else:
                num_bits = _round_bits_to_nearest_byte(num_bits)
                el_byte_len = element.byte_len()
                if el_byte_len is None:
                    el_byte_len = _U16_NUM_BYTES
                num_bits += el_byte_len * 8
            if self._homogenous_element:
                num_bits *= len(self.elements)
                break
        return _bits_to_byte(num_bits)

    def encode(self, value: Sequence | bytes | bytearray) -> bytes:
        if len(value) != len(self.elements):
            raise ValueError(f"expected {len(self.elements)} elements: {_error_str(value)}")
        if _is_byte(self._homogenous_element):
            return bytes(value)
        head = bytearray()
        tail = bytearray()
        bit_index = 0
        tail_offset = self._head_num_bytes
        for el, el_type in zip(value, self.elements, strict=True):
            # there are 3 kinds of elements to consider when encoding a tuple
            # 1. bool, these require packing consecutive values into a byte in the head
            # 2. dynamically sized types, these require a pointer in the head and the actual data in the tail
            # 3. statically sized types, these are stored directly in the head
            if _is_bool(el_type):
                # append a new value if start of a new byte
                if bit_index % 8 == 0:
                    head.append(0)
                if el is True:
                    head[-1] = _set_bit(head[-1], bit_index % 8)
                elif el is False:
                    pass
                else:
                    raise ValueError("expected bool")
                bit_index += 1
            else:
                bit_index = 0
                el_bytes = el_type.encode(el)
                if el_type.is_dynamic():
                    try:
                        head.extend(_int_to_u16_bytes(tail_offset))
                    except OverflowError:
                        raise ValueError(f"encoded bytes length exceeds {_MAX_U16}") from None
                    tail_offset += len(el_bytes)
                    tail.extend(el_bytes)
                else:
                    head.extend(el_bytes)
        return bytes((*head, *tail))

    @cached_property
    def _tuple_head_offsets(self) -> Mapping[int, int]:
        offsets = {}
        num_bits = 0
        for idx, element in enumerate(self.elements):
            if element.is_dynamic():
                offsets[idx] = _bits_to_byte(num_bits)
            if _is_bool(element):
                num_bits += 1
            else:
                num_bits = _round_bits_to_nearest_byte(num_bits)
                el_byte_len = element.byte_len()
                if el_byte_len is None:
                    el_byte_len = _U16_NUM_BYTES
                num_bits += el_byte_len * 8
        return offsets

    def _get_next_dynamic_head_offset(self, index: int, value: memoryview) -> int | None:
        # the last element reads to end
        if index == len(self.elements) - 1:
            return None
        if self._homogenous_element:
            assert self._homogenous_element.is_dynamic()
            next_head_offset = _U16_NUM_BYTES * (index + 1)
        else:
            for idx in range(index + 1, len(self.elements)):
                try:
                    next_head_offset = self._tuple_head_offsets[idx]
                except KeyError:
                    continue
                else:
                    break
            else:
                return None
        return _u16_bytes_to_int(value[next_head_offset : next_head_offset + _U16_NUM_BYTES])

    def decode(self, value: BytesLike) -> tuple | bytes:
        self._check_num_bytes(value)
        if _is_byte(self._homogenous_element):
            return bytes(value)

        value = memoryview(value)
        result = []
        head_offset = 0
        bit_index = 0
        expected_tail_offset = self._head_num_bytes
        for el_idx, el_type in enumerate(self.elements):
            if _is_bool(el_type):
                current_byte = value[head_offset + bit_index // 8]
                bool_value = _get_bit(current_byte, bit_index % 8)
                result.append(bool_value)
                bit_index += 1
            else:
                head_offset += _bits_to_byte(bit_index)
                bit_index = 0
                el_byte_len = el_type.byte_len()
                if el_byte_len is None:
                    el_offset = _u16_bytes_to_int(value[head_offset : head_offset + _U16_NUM_BYTES])
                    if el_offset != expected_tail_offset:
                        raise ValueError(f"expected tail offset of {expected_tail_offset} got: {el_offset}")
                    head_offset += _U16_NUM_BYTES
                    next_el_offset = self._get_next_dynamic_head_offset(el_idx, value)
                    el_bytes = value[el_offset:next_el_offset]
                    expected_tail_offset += len(el_bytes)
                    result.append(el_type.decode(el_bytes))
                else:
                    result.append(el_type.decode(value[head_offset : head_offset + el_byte_len]))
                    head_offset += el_byte_len
        if self.is_dynamic() and expected_tail_offset != len(value):
            raise ValueError(f"expected {expected_tail_offset} bytes for {self.display_name}, got {len(value)} bytes")
        return tuple(result)


@typing.final
@dataclasses.dataclass(frozen=True, kw_only=True)
class StructType(ABIType):
    struct_name: str
    fields: Mapping[str, ABIType]
    decode_type: type = dataclasses.field(default=dict)

    @property
    def display_name(self) -> str:
        return self.struct_name

    @cached_property
    def name(self) -> str:
        return self._tuple_type.name

    @cached_property
    def _tuple_type(self) -> TupleType:
        return TupleType(elements=tuple(self.fields.values()))

    def byte_len(self) -> int | None:
        return self._tuple_type.byte_len()

    def encode(self, value: dict[str, typing.Any] | tuple | object) -> bytes:
        if isinstance(value, dict):  # structs as a dictionary mapped by field name
            field_values = tuple(value[field_name] for field_name in self.fields)
        elif isinstance(value, tuple):  # structs that have already been converted to a tuple
            field_values = value
        else:  # objects with struct field names
            field_values = tuple(getattr(value, field_name) for field_name in self.fields)
        return self._tuple_type.encode(field_values)

    def decode(self, value: BytesLike) -> typing.Any:  # noqa: ANN401
        field_values = self._tuple_type.decode(value)
        fields = dict(zip(self.fields, field_values, strict=True))
        return self.decode_type(**fields)

    def __hash__(self) -> int:
        return hash(self.display_name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StructType):
            return False
        return (
            self.display_name == other.display_name
            and self.fields.keys() == other.fields.keys()
            and self._tuple_type == other._tuple_type
        )


@typing.final
@dataclasses.dataclass(frozen=True)
class StringType(ABIType):
    _array_type: DynamicArrayType = dataclasses.field(default=DynamicArrayType(element=ByteType()), init=False)

    @property
    def name(self) -> str:
        return "string"

    def byte_len(self) -> None:
        return None

    def encode(self, value: str) -> bytes:
        if not isinstance(value, str):
            raise TypeError("expected str")
        return self._array_type.encode(value.encode("utf-8"))

    def decode(self, value: BytesLike) -> str:
        bytes_ = self._array_type.decode(value)
        assert isinstance(bytes_, bytes)
        return bytes_.decode("utf-8")


@typing.final
@dataclasses.dataclass(frozen=True)
class AddressType(ABIType):
    _array_type: StaticArrayType = dataclasses.field(default=StaticArrayType(element=ByteType(), size=32), init=False)

    @property
    def name(self) -> str:
        return "address"

    def byte_len(self) -> int | None:
        return self._array_type.byte_len()

    def encode(self, value: str | bytes | bytearray) -> bytes:
        if isinstance(value, str):
            value = public_key_from_address(value)
        return self._array_type.encode(value)

    def decode(self, value: BytesLike) -> str:
        public_key = self._array_type.decode(value)
        assert isinstance(public_key, bytes)
        return address_from_public_key(public_key)


def _is_bool(typ: ABIType | None) -> bool:
    return type(typ) is BoolType


def _is_byte(typ: ABIType | None) -> bool:
    return type(typ) is ByteType


_COMMON_TYPES = {
    **{f"uint{n}": UintType(n) for n in range(8, _MAX_UINT_N + 1, 8)},
    "byte": ByteType(),
    "bool": BoolType(),
    "address": AddressType(),
    "string": StringType(),
}


def split_tuple_str(s: str) -> Iterator[str]:
    """
    Split a well-formed tuple into it's top level elements

    e.g. "(uint64,(bool,uint8),uint32)"
    """
    if not s:
        return

    if s.startswith(",") or s.endswith(","):
        raise ValueError(f"cannot have leading or trailing commas in ({s})")

    depth = 0
    current_element = ""
    for char in s:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            # yield only top level tuple elements, nested elements will be recursively parsed
            if not current_element:
                raise ValueError(f"commas must follow a tuple element: ({s})")
            yield current_element
            current_element = ""
            continue
        current_element += char
    if current_element:
        yield current_element
    if depth != 0:
        raise ValueError(f"parenthesis mismatch: ({s})")


def _set_bit(value: int, bit_index: int) -> int:
    return value | (_ABI_BOOL_TRUE_UINT >> bit_index)


def _get_bit(value: int, bit_index: int) -> bool:
    return (value & (_ABI_BOOL_TRUE_UINT >> bit_index)) != 0


def _int_to_u16_bytes(value: int) -> bytes:
    return value.to_bytes(length=_U16_NUM_BYTES, byteorder="big", signed=False)


def _u16_bytes_to_int(value: memoryview) -> int:
    if value.nbytes != _U16_NUM_BYTES:
        raise ValueError("expected uint16 bytes")
    return int.from_bytes(value, byteorder="big", signed=False)


def _bits_to_byte(bits: int) -> int:
    return (bits + 7) // 8


def _round_bits_to_nearest_byte(bits: int) -> int:
    return _bits_to_byte(bits) * 8


def _error_str(value: object) -> str:
    if isinstance(value, bytes | bytearray | memoryview):
        return f"0x{value.hex()}"
    else:
        return str(value)
