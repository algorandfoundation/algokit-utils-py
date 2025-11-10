# AUTO-GENERATED: oas_generator
import base64
from binascii import Error as BinasciiError
from collections.abc import Callable, Iterable, Mapping
from dataclasses import is_dataclass
from enum import Enum
from typing import TypeAlias, TypeVar

from algokit_common.serde import from_wire, to_wire

T = TypeVar("T")
E = TypeVar("E", bound=Enum)
KT = TypeVar("KT")
BytesLike: TypeAlias = bytes | bytearray | memoryview


def _coerce_bytes(value: bytes | bytearray | memoryview) -> bytes:
    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, bytearray):
        return bytes(value)
    return value


def encode_bytes_base64(value: BytesLike) -> str:
    return base64.b64encode(_coerce_bytes(value)).decode("ascii")


def decode_bytes_base64(raw: object) -> bytes:
    if isinstance(raw, bytes | bytearray | memoryview):
        return bytes(raw)
    if isinstance(raw, str):
        try:
            return base64.b64decode(raw.encode("ascii"), validate=True)
        except (BinasciiError, UnicodeEncodeError):
            try:
                return raw.encode("utf-8")
            except UnicodeEncodeError as fallback_exc:
                raise ValueError("Invalid base64 payload") from fallback_exc
    raise TypeError(f"Unsupported value for bytes field: {type(raw)!r}")


def encode_bytes_sequence(values: Iterable[BytesLike | None] | None) -> list[str | None] | None:
    if values is None:
        return None
    encoded: list[str | None] = []
    for value in values:
        if value is None:
            encoded.append(None)
            continue
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError(f"Unsupported value for bytes field sequence: {type(value)!r}")
        encoded.append(encode_bytes_base64(value))
    return encoded or None


def decode_bytes_sequence(raw: object) -> list[bytes | None] | None:
    if not isinstance(raw, list):
        return None
    decoded: list[bytes | None] = []
    for item in raw:
        if item is None:
            decoded.append(None)
            continue
        decoded.append(decode_bytes_base64(item))
    return decoded or None


def encode_model_sequence(values: Iterable[object] | None) -> list[dict[str, object]] | None:
    if values is None:
        return None
    encoded: list[dict[str, object]] = []
    for value in values:
        if value is None:
            continue
        encoded.append(to_wire(value))
    return encoded or None


def decode_model_sequence(cls_factory: Callable[[], type[T]], raw: object) -> list[T] | None:
    if not isinstance(raw, list):
        return None
    cls = cls_factory()
    decoded: list[T] = []
    for item in raw:
        if isinstance(item, Mapping):
            decoded.append(from_wire(cls, item))
    return decoded or None


def encode_enum_sequence(values: Iterable[object] | None) -> list[object] | None:
    if values is None:
        return None
    encoded: list[object] = []
    for value in values:
        if value is None:
            continue
        encoded.append(value.value if hasattr(value, "value") else value)
    return encoded or None


def decode_enum_sequence(enum_factory: Callable[[], type[E]], raw: object) -> list[E] | None:
    if not isinstance(raw, list):
        return None
    enum_cls = enum_factory()
    decoded: list[E] = []
    for item in raw:
        try:
            decoded.append(enum_cls(item))
        except Exception:
            continue
    return decoded or None


def encode_model_mapping(
    factory: Callable[[], type[T]],
    mapping: Mapping[object, object] | None,
    *,
    key_encoder: Callable[[object], str] | None = None,
) -> dict[str, object] | None:
    if mapping is None:
        return None
    cls = factory()
    encoded: dict[str, object] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        encoded_key: str
        if key_encoder is not None:
            encoded_key = key_encoder(key)
        elif isinstance(key, str):
            encoded_key = key
        else:
            encoded_key = str(key)
        if isinstance(value, cls) or is_dataclass(value):
            encoded[encoded_key] = to_wire(value)
        else:
            encoded[encoded_key] = value
    return encoded or None


def decode_model_mapping(
    factory: Callable[[], type[T]],
    raw: object,
    *,
    key_decoder: Callable[[object], KT] | None = None,
) -> dict[KT, T] | None:
    if not isinstance(raw, Mapping):
        return None
    cls = factory()
    decoded: dict[KT, T] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping):
            decoded_key = key_decoder(key) if key_decoder is not None else key
            decoded[decoded_key] = from_wire(cls, value)
    return decoded or None


def mapping_encoder(
    factory: Callable[[], type[T]],
    *,
    key_encoder: Callable[[object], str] | None = None,
) -> Callable[[Mapping[object, object] | None], dict[str, object] | None]:
    def _encode(mapping: Mapping[object, object] | None) -> dict[str, object] | None:
        return encode_model_mapping(factory, mapping, key_encoder=key_encoder)

    return _encode


def mapping_decoder(
    factory: Callable[[], type[T]],
    *,
    key_decoder: Callable[[object], KT] | None = None,
) -> Callable[[object], dict[KT, T] | None]:
    def _decode(raw: object) -> dict[KT, T] | None:
        return decode_model_mapping(factory, raw, key_decoder=key_decoder)

    return _decode
