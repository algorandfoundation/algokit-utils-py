from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import is_dataclass
from typing import TypeVar

from algokit_common.serde import from_wire, to_wire

T = TypeVar("T")
E = TypeVar("E")


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
    factory: Callable[[], type[T]], mapping: Mapping[str, object] | None
) -> dict[str, object] | None:
    if mapping is None:
        return None
    cls = factory()
    encoded: dict[str, object] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        if isinstance(value, cls) or is_dataclass(value):
            encoded[str(key)] = to_wire(value)
        else:
            encoded[str(key)] = value
    return encoded or None


def decode_model_mapping(factory: Callable[[], type[T]], raw: object) -> dict[str, T] | None:
    if not isinstance(raw, Mapping):
        return None
    cls = factory()
    decoded: dict[str, T] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping):
            decoded[str(key)] = from_wire(cls, value)
    return decoded or None


def mapping_encoder(
    factory: Callable[[], type[T]],
) -> Callable[[Mapping[str, object] | None], dict[str, object] | None]:
    def _encode(mapping: Mapping[str, object] | None) -> dict[str, object] | None:
        return encode_model_mapping(factory, mapping)

    return _encode


def mapping_decoder(factory: Callable[[], type[T]]) -> Callable[[object], dict[str, T] | None]:
    def _decode(raw: object) -> dict[str, T] | None:
        return decode_model_mapping(factory, raw)

    return _decode
