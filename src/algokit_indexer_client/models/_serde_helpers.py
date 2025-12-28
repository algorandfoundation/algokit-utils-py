# AUTO-GENERATED: oas_generator
import base64
from binascii import Error as BinasciiError
from collections.abc import Callable, Iterable, Mapping
from dataclasses import is_dataclass
from enum import Enum
from typing import TypeAlias, TypeVar

from algokit_common.serde import from_wire, to_wire

DecodedT = TypeVar("DecodedT")
EnumValueT = TypeVar("EnumValueT", bound=Enum)
MapKeyT = TypeVar("MapKeyT")
BytesLike: TypeAlias = bytes | bytearray | memoryview


def _coerce_bytes(value: bytes | bytearray | memoryview) -> bytes:
    if isinstance(value, memoryview | bytearray):
        return bytes(value)
    return value


def encode_bytes(value: BytesLike) -> str:
    return base64.b64encode(_coerce_bytes(value)).decode("ascii")


def decode_bytes(raw: object) -> bytes:
    """Decode bytes that may be raw (msgpack) or base64-encoded (JSON)."""
    if isinstance(raw, bytes | bytearray | memoryview):
        return bytes(raw)
    if isinstance(raw, str):
        try:
            return base64.b64decode(raw.encode("ascii"), validate=True)
        except (BinasciiError, UnicodeEncodeError) as exc:
            raise ValueError("Invalid base64 payload") from exc
    raise TypeError(f"Unsupported value for bytes field: {type(raw)!r}")


def decode_bytes_base64(raw: object) -> bytes:
    """Decode bytes that are always base64-encoded strings (even in msgpack).

    Used for fields marked with x-algokit-bytes-base64 in the OpenAPI spec.
    These fields contain base64-encoded strings in both JSON and msgpack responses.
    """
    if isinstance(raw, bytes | bytearray | memoryview | str):
        try:
            return base64.b64decode(raw, validate=True)
        except (BinasciiError, ValueError, UnicodeEncodeError) as exc:
            raise ValueError("Invalid base64 payload") from exc
    raise TypeError(f"Unsupported value for bytes field: {type(raw)!r}")


def encode_fixed_bytes(value: BytesLike, expected_length: int) -> str:
    """Encode fixed-length bytes to base64, validating the length."""
    coerced = _coerce_bytes(value)
    if len(coerced) != expected_length:
        raise ValueError(f"Expected {expected_length} bytes, got {len(coerced)}")
    return base64.b64encode(coerced).decode("ascii")


def decode_fixed_bytes(raw: object, expected_length: int) -> bytes:
    """Decode base64 to fixed-length bytes, validating the length."""
    decoded = decode_bytes(raw)
    if len(decoded) != expected_length:
        raise ValueError(f"Expected {expected_length} bytes, got {len(decoded)}")
    return decoded


def decode_bytes_map_key(raw: object) -> bytes:
    if isinstance(raw, bytes | bytearray | memoryview):
        return bytes(raw)
    if isinstance(raw, str):
        # note: this is undoing the implicit bytes -> str conversion that
        # _coerce_msgpack_key does in client.py
        # as long as "strict" was used to encode the str then this should be safe
        try:
            return raw.encode("utf-8", errors="strict")
        except UnicodeEncodeError as fallback_exc:
            raise ValueError("Invalid bytes map key") from fallback_exc
    raise TypeError(f"Unsupported map key for bytes field: {type(raw)!r}")


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
        encoded.append(encode_bytes(value))
    return encoded or None


def decode_bytes_sequence(raw: object) -> list[bytes | None] | None:
    if not isinstance(raw, list):
        return None
    decoded: list[bytes | None] = []
    for item in raw:
        if item is None:
            decoded.append(None)
            continue
        decoded.append(decode_bytes(item))
    return decoded or None


def encode_fixed_bytes_sequence(
    values: Iterable[BytesLike | None] | None, expected_length: int
) -> list[str | None] | None:
    """Encode a sequence of fixed-length bytes to base64, validating each element's length."""
    if values is None:
        return None
    encoded: list[str | None] = []
    for value in values:
        if value is None:
            encoded.append(None)
            continue
        if not isinstance(value, bytes | bytearray | memoryview):
            raise TypeError(f"Unsupported value for bytes field sequence: {type(value)!r}")
        encoded.append(encode_fixed_bytes(value, expected_length))
    return encoded or None


def decode_fixed_bytes_sequence(raw: object, expected_length: int) -> list[bytes | None] | None:
    """Decode a sequence of base64 strings to fixed-length bytes, validating each element's length."""
    if not isinstance(raw, list):
        return None
    decoded: list[bytes | None] = []
    for item in raw:
        if item is None:
            decoded.append(None)
            continue
        decoded.append(decode_fixed_bytes(item, expected_length))
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


def decode_model_sequence(cls_factory: Callable[[], type[DecodedT]], raw: object) -> list[DecodedT] | None:
    if not isinstance(raw, list):
        return None
    cls = cls_factory()
    decoded: list[DecodedT] = []
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


def decode_enum_sequence(enum_factory: Callable[[], type[EnumValueT]], raw: object) -> list[EnumValueT] | None:
    if not isinstance(raw, list):
        return None
    enum_cls = enum_factory()
    decoded: list[EnumValueT] = []
    for item in raw:
        try:
            decoded.append(enum_cls(item))
        except Exception:
            continue
    return decoded or None


def encode_model_mapping(
    factory: Callable[[], type[DecodedT]],
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
    factory: Callable[[], type[DecodedT]],
    raw: object,
    *,
    key_decoder: Callable[[object], MapKeyT] | None = None,
) -> dict[MapKeyT, DecodedT] | None:
    if not isinstance(raw, Mapping):
        return None
    cls = factory()
    decoded: dict[MapKeyT, DecodedT] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping):
            decoded_key = key_decoder(key) if key_decoder is not None else key
            decoded[decoded_key] = from_wire(cls, value)
    return decoded or None


def decode_optional_bool(raw: object) -> bool | None:
    if raw is None:
        return None
    return bool(raw)


def mapping_encoder(
    factory: Callable[[], type[DecodedT]],
    *,
    key_encoder: Callable[[object], str] | None = None,
) -> Callable[[Mapping[object, object] | None], dict[str, object] | None]:
    def _encode(mapping: Mapping[object, object] | None) -> dict[str, object] | None:
        return encode_model_mapping(factory, mapping, key_encoder=key_encoder)

    return _encode


def mapping_decoder(
    factory: Callable[[], type[DecodedT]],
    *,
    key_decoder: Callable[[object], MapKeyT] | None = None,
) -> Callable[[object], dict[MapKeyT, DecodedT] | None]:
    def _decode(raw: object) -> dict[MapKeyT, DecodedT] | None:
        return decode_model_mapping(factory, raw, key_decoder=key_decoder)

    return _decode
