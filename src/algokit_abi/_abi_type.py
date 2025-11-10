import abc
import dataclasses
import decimal
import typing
from collections.abc import Collection, Iterator, Mapping, Sequence
from functools import cached_property

from algokit_common import address_from_public_key, public_key_from_address

BytesLike = bytes | bytearray | memoryview


class ABIType(abc.ABC):
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
            tup_elements = [cls.from_string(t) for t in _parse_tuple(tup_inner)]
            return TupleType(tup_elements)
        if value.endswith("[]"):
            element = cls.from_string(value[:-2])
            return DynamicArrayType(element)
        if value.endswith("]"):
            array_start = value.rindex("[")
            size_str = value[array_start + 1 : -1]
            size = int(size_str)
            element = cls.from_string(value[:array_start])
            return StaticArrayType(element, size)
        if value.startswith("ufixed"):
            n_m_str = value.removeprefix("ufixed")
            n_str, m_str = n_m_str.split("x")
            n = int(n_str)
            m = int(m_str)
            return UfixedType(n, m)
        # TODO: what about StructType
        raise ValueError(f"unknown abi type: {value}")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ABIType):
            return self.name == other.name
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name


_ABI_BOOL_TRUE_UINT = 0x80
_ABI_BOOL_TRUE = _ABI_BOOL_TRUE_UINT.to_bytes(length=1, byteorder="big")
_ABI_BOOL_FALSE = b"\x00"


class BoolType(ABIType):
    @property
    def name(self) -> str:
        return "bool"

    def byte_len(self) -> int:
        return 1

    def encode(self, value: bool) -> bytes:  # noqa: FBT001
        # intentionally comparing to True and False to handle invalid types
        if value is True:
            return _ABI_BOOL_TRUE
        elif value is False:
            return _ABI_BOOL_FALSE
        else:
            raise ValueError(f"expected a bool: {value}")

    def decode(self, value: BytesLike) -> bool:
        if value == _ABI_BOOL_TRUE:
            return True
        elif value == _ABI_BOOL_FALSE:
            return False
        else:
            raise ValueError("bool value could not be decoded")


_U16_SIZE = 2


@dataclasses.dataclass(frozen=True)
class DynamicArrayType(ABIType):
    element: ABIType

    @property
    def name(self) -> str:
        return f"{self.element.name}[]"

    def byte_len(self) -> None:
        return None

    def encode(self, value: Sequence | bytes | bytearray) -> bytes:
        static_type = StaticArrayType(element=self.element, size=len(value))
        return _int_to_u16_bytes(len(value)) + static_type.encode(value)

    def decode(self, value: BytesLike) -> list | bytes:
        data = memoryview(value)
        if data.nbytes < _U16_SIZE:
            raise ValueError(f"not enough bytes to decode {self.element}: {value!r}")

        array_len = int.from_bytes(data[:_U16_SIZE], byteorder="big")

        static_type = StaticArrayType(element=self.element, size=array_len)
        return static_type.decode(data[_U16_SIZE:])


@dataclasses.dataclass(frozen=True)
class _RepeatedCollection(Collection[ABIType]):
    element: ABIType
    size: int

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[ABIType]:
        for _ in range(self.size):
            yield self.element

    def __contains__(self, x: object, /) -> bool:
        return x == self.element


@dataclasses.dataclass(frozen=True)
class StaticArrayType(ABIType):
    element: ABIType
    size: int

    @property
    def name(self) -> str:
        return f"{self.element.name}[{self.size}]"

    @cached_property
    def _tuple_type(self) -> "TupleType":
        return TupleType(elements=_RepeatedCollection(self.element, self.size))

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


@dataclasses.dataclass(frozen=True)
class TupleType(ABIType):
    elements: Collection[ABIType]

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
            if isinstance(self.elements, _RepeatedCollection):
                total_bits *= self.elements.size
                break
        return _bits_to_byte(total_bits)

    @cached_property
    def _head_num_bytes(self) -> int:
        num_bits = 0
        for element in self.elements:
            if element.name == "bool":
                num_bits += 1
            else:
                num_bits = _round_bits_to_nearest_byte(num_bits)
                el_byte_len = element.byte_len()
                if el_byte_len is None:
                    el_byte_len = _U16_SIZE
                num_bits += el_byte_len * 8
            if isinstance(self.elements, _RepeatedCollection):
                num_bits *= self.elements.size
                break
        return _bits_to_byte(num_bits)

    def encode(self, value: Sequence | bytes | bytearray) -> bytes:
        if len(value) != len(self.elements):
            raise ValueError(f"expected {len(self.elements)} elements: {value!r}")
        head = bytearray()
        tail = bytearray()
        bit_index = 0
        tail_offset = self._head_num_bytes
        for el, el_type in zip(value, self.elements, strict=True):
            if el_type.name == "bool":
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
                    head.extend(_int_to_u16_bytes(tail_offset))
                    tail_offset += len(el_bytes)
                    tail.extend(el_bytes)
                else:
                    head.extend(el_bytes)
        return bytes((*head, *tail))

    def decode(self, value: BytesLike) -> tuple | bytes:
        value = memoryview(value)
        if all(el.name == "byte" for el in self.elements):
            if value.nbytes != len(self.elements):
                raise ValueError(f"expected {len(self.elements)} bytes: {value!r}")
            return bytes(value)
        result = []
        head_offset = 0
        bool_idx = 0
        last_idx = len(self.elements) - 1
        for el_idx, el_type in enumerate(self.elements):
            if el_type.name == "bool":
                result.append(_get_bit(value[head_offset], bool_idx))
                bool_idx += 1
                if bool_idx % 8 == 0:
                    bool_idx = 0
                    head_offset += 1
            else:
                if bool_idx:
                    bool_idx = 0
                    head_offset += 1
                el_byte_len = el_type.byte_len()
                if el_byte_len is None:
                    el_offset = _u16_bytes_to_int(value[head_offset : head_offset + _U16_SIZE])
                    head_offset += _U16_SIZE
                    next_el_offset = None
                    if el_idx != last_idx:
                        next_el_offset = _u16_bytes_to_int(value[head_offset : head_offset + _U16_SIZE])
                    el_bytes = value[el_offset:next_el_offset]
                    result.append(el_type.decode(el_bytes))
                else:
                    result.append(el_type.decode(value[head_offset : head_offset + el_byte_len]))
                    head_offset += el_byte_len
        return tuple(result)


@dataclasses.dataclass(frozen=True)
class StructType(ABIType):
    fields: Mapping[str, ABIType]
    decode_type: type = dataclasses.field(default=dict)

    @cached_property
    def name(self) -> str:
        return f"({','.join(f'{f}={v.name}' for f, v in self.fields.items())})"

    @cached_property
    def _tuple_type(self) -> TupleType:
        return TupleType(elements=tuple(self.fields.values()))

    def byte_len(self) -> int | None:
        return self._tuple_type.byte_len()

    def encode(self, value: typing.Any) -> bytes:  # noqa: ANN401
        field_values = tuple(_get_field(value, field_name) for field_name in self.fields)
        return self._tuple_type.encode(field_values)

    def decode(self, value: BytesLike) -> typing.Any:  # noqa: ANN401
        field_values = self._tuple_type.decode(value)
        fields = dict(zip(self.fields, field_values, strict=True))
        return self.decode_type(**fields)


_MAX_UINTN = 512


@dataclasses.dataclass(frozen=True)
class UintType(ABIType):
    bit_size: int = dataclasses.field()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.bit_size, int)
            or self.bit_size <= 0
            or self.bit_size > _MAX_UINTN
            or self.bit_size % 8 != 0
        ):
            raise ValueError(f"bit_size must be between 8 and {_MAX_UINTN} and divisible by 8")

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
        if len(value) != self.byte_len():
            raise ValueError(f"incorrect number of bytes to decode {self.name}: {value!r}")
        return int.from_bytes(value, byteorder="big", signed=False)


_MAX_PRECISION = 160


@dataclasses.dataclass(frozen=True)
class UfixedType(ABIType):
    bit_size: int
    precision: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.bit_size, int)
            or self.bit_size <= 0
            or self.bit_size > _MAX_UINTN
            or self.bit_size % 8 != 0
        ):
            raise ValueError(f"bit_size must be between 8 and {_MAX_UINTN} and divisible by 8")
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
            value_int = int(value * 10**self.precision)
        else:
            value_int = value
        return self._int_type.encode(value_int)

    def decode(self, value: BytesLike) -> decimal.Decimal:
        int_str = str(self._int_type.decode(value))
        decimal_str = int_str[: -self.precision] + "." + int_str[-self.precision :]
        return decimal.Decimal(decimal_str)


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
            raise ValueError(f"expected 1 byte: {value!r}")

    def decode(self, value: BytesLike) -> bytes:
        if len(value) == 1:
            return bytes(value)
        else:
            raise ValueError(f"expected 1 byte: {value!r}")


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


_COMMON_TYPES = {
    **{f"uint{n}": UintType(n) for n in range(8, _MAX_UINTN + 1, 8)},
    "byte": ByteType(),
    "bool": BoolType(),
    "address": AddressType(),
    "string": StringType(),
}


def _parse_tuple(s: str) -> Iterator[str]:
    if not s:
        return

    if s.startswith(",") or s.endswith(","):
        raise ValueError(f"cannot have leading or trailing commas in {s}")

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
                raise ValueError(f"commas must follow a tuple element: {s}")
            yield current_element
            current_element = ""
            continue
        current_element += char
    if current_element:
        yield current_element
    if depth != 0:
        raise ValueError(f"parenthesis mismatch: {s}")


def _set_bit(value: int, bit_index: int) -> int:
    return value | (_ABI_BOOL_TRUE_UINT >> bit_index)


def _get_bit(value: int, bit_index: int) -> bool:
    return (value & (_ABI_BOOL_TRUE_UINT >> bit_index)) != 0


def _int_to_u16_bytes(value: int) -> bytes:
    return value.to_bytes(length=_U16_SIZE, byteorder="big", signed=False)


def _u16_bytes_to_int(value: memoryview) -> int:
    assert value.nbytes == _U16_SIZE, "expected uint16 bytes"
    return int.from_bytes(value, byteorder="big", signed=False)


def _bits_to_byte(bits: int) -> int:
    return (bits + 7) // 8


def _round_bits_to_nearest_byte(bits: int) -> int:
    return _bits_to_byte(bits) * 8


def _get_field(obj: typing.Any, field_name: str) -> typing.Any:  # noqa: ANN401
    try:
        return getattr(obj, field_name)
    except AttributeError:
        return obj[field_name]
