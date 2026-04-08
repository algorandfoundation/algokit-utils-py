import base64
import typing
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from algokit_abi import abi
from algokit_common import from_wire, to_wire, wire

_Metadata = Mapping[str, object]
_T = typing.TypeVar("_T")


def base64_encoded_bytes(alias: str) -> _Metadata:
    return wire(
        alias,
        encode=lambda v: base64.b64encode(v).decode("ascii"),
        decode=base64.b64decode,
    )


def sequence(alias: str, typ: Callable[..., object], *, omit_empty_seq: bool = True) -> _Metadata:
    def decode(payload: list) -> object:
        return [typ(v) for v in payload]

    return wire(alias, decode=decode, omit_empty_seq=omit_empty_seq)


def nested_sequence(alias: str, typ: type[_T]) -> _Metadata:
    def encode(val: list | None) -> object:
        if val is None:
            return None
        return [to_wire(v) for v in val]

    def decode(payload: list | None) -> object:
        if payload is None:
            return None
        return [from_wire(typ, v) for v in payload]

    return wire(alias, encode=encode, decode=decode, omit_empty_seq=False, omit_if_none=True)


def mapping(alias: str, typ: type[_T]) -> _Metadata:
    def encode(value: Mapping) -> Mapping:
        return {k: to_wire(v) for k, v in value.items()}

    def decode(payload: Mapping) -> Mapping:
        return {k: from_wire(typ, v) for k, v in payload.items()}

    return wire(alias, decode=decode, encode=encode)


def abi_type(alias: str) -> _Metadata:
    def encode(value: object) -> str:
        if isinstance(value, abi.ABIType):
            return value.name
        else:
            return str(value)

    def decode(value: str) -> object:
        from algokit_abi import arc56

        try:
            return arc56.ENUM_ALIASES[value]
        except KeyError:
            return abi.ABIType.from_string(value)

    return wire(alias, encode=encode, decode=decode)


def storage(alias: str) -> _Metadata:
    def encode(value: object) -> str:
        if isinstance(value, abi.ABIType):
            return value.name
        else:
            return str(value)

    def decode(value: str) -> object:
        from algokit_abi import arc56

        try:
            return arc56.AVMType(value)
        except ValueError:
            pass
        try:
            return abi.ABIType.from_string(value)
        except ValueError:
            return str(value)

    return wire(alias, encode=encode, decode=decode)


class _StructField(typing.TypedDict):
    name: str
    type: "str | list[_StructField]"


_StructFieldJson = dict[str, list[_StructField]]


@dataclass
class _StructDecoder:
    _struct_json: _StructFieldJson
    result: dict[str, abi.StructType] = field(default_factory=dict)

    @classmethod
    def decode(cls, struct_json: _StructFieldJson) -> dict[str, abi.StructType]:
        decoder = cls(struct_json)
        decoder._process()
        return decoder.result

    def _process(self) -> None:
        # add known struct names
        for struct_name, struct_json in self._struct_json.items():
            self._get_or_add(struct_name, struct_json)

    def _get_or_add(self, name: str, fields: Sequence[_StructField]) -> abi.StructType:
        try:
            return self.result[name]
        except KeyError:
            pass
        self.result[name] = struct = self._decode_struct(name, fields)
        return struct

    def _decode_struct(self, name: str, fields: Sequence[_StructField]) -> abi.StructType:
        abi_fields = dict[str, abi.ABIType]()
        for field_ in fields:
            field_name = field_["name"]
            field_type = field_["type"]
            if isinstance(field_type, Sequence) and not isinstance(field_type, str):  # anonymous inner struct
                inner_struct_name = f"{name}_{field_name}"
                field_abi_type: abi.ABIType = self._decode_struct(inner_struct_name, field_type)
            elif (field_struct_json := self._struct_json.get(field_type)) is not None:  # named struct
                field_abi_type = self._get_or_add(field_type, field_struct_json)
            else:
                field_abi_type = abi.ABIType.from_string(field_type)
            abi_fields[field_name] = field_abi_type
        return abi.StructType(struct_name=name, fields=abi_fields)


def _encode_structs(structs: dict[str, abi.StructType]) -> dict:
    return {name: _encode_struct(structs, struct) for name, struct in structs.items()}


def _encode_struct(structs: dict[str, abi.StructType], struct: abi.StructType) -> list:
    fields = []
    for field_name, field_type in struct.fields.items():
        fields.append(_StructField(name=field_name, type=_encode_struct_field(structs, field_type)))
    return fields


def _encode_struct_field(structs: dict[str, abi.StructType], field_type: abi.ABIType) -> str | list:
    if isinstance(field_type, abi.StructType):
        if field_type.display_name in structs:
            return field_type.display_name
        else:
            return _encode_struct(structs, field_type)
    else:
        return field_type.name


struct_metadata = wire("structs", encode=_encode_structs, decode=_StructDecoder.decode)
