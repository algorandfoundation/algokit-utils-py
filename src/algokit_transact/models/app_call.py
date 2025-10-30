from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import cast

from algokit_transact.codec.serde import (
    DecodeError,
    EncodeError,
    addr_seq,
    bytes_seq,
    enum_value,
    int_seq,
    nested,
    wire,
)
from algokit_transact.models.common import OnApplicationComplete, StateSchema


@dataclass(slots=True, frozen=True)
class BoxReference:
    app_id: int = 0
    name: bytes = b""

    def __post_init__(self) -> None:  # pragma: no cover - trivial setters
        object.__setattr__(self, "app_id", int(self.app_id))
        object.__setattr__(self, "name", bytes(self.name))


@dataclass(slots=True, frozen=True)
class _WireBoxReference:
    index: int
    name: bytes


def _coerce_box_sequence(
    boxes: Iterable[BoxReference | _WireBoxReference],
) -> tuple[BoxReference | _WireBoxReference, ...]:
    if isinstance(boxes, tuple):
        return boxes
    return tuple(boxes)


def _normalize_box_reference(
    app_call: AppCallTransactionFields,
    ref: BoxReference | _WireBoxReference,
) -> BoxReference:
    if isinstance(ref, BoxReference):
        return ref
    if isinstance(ref, _WireBoxReference):
        app_id = _map_box_index_to_app_id(ref.index, app_call)
        return BoxReference(app_id=app_id, name=ref.name)
    raise TypeError("Unsupported box reference payload")


def _map_box_index_to_app_id(index: int, app_call: AppCallTransactionFields) -> int:
    if index == 0:
        return app_call.app_id
    app_refs = tuple(app_call.app_references or ())
    pos = index - 1
    if pos < 0 or pos >= len(app_refs):
        raise DecodeError(
            "Box reference index is out of bounds for application references",
        )
    return app_refs[pos]


def _map_box_app_id_to_index(
    app_id: int,
    app_call: AppCallTransactionFields,
    app_refs: tuple[int, ...],
) -> int:
    if app_id in (0, app_call.app_id):
        return 0
    try:
        pos = app_refs.index(app_id)
    except ValueError as exc:
        raise EncodeError(
            "Box reference app id must exist in application references",
        ) from exc
    return pos + 1


def _encode_box_references(
    app_call: AppCallTransactionFields,
    value: object,
) -> list[dict[str, object]] | None:
    if value is None:
        return None
    if not isinstance(value, Iterable):
        raise EncodeError("Box references must be iterable")
    raw_refs = _coerce_box_sequence(cast(Iterable[BoxReference | _WireBoxReference], value))
    if not raw_refs:
        return None

    app_refs = tuple(app_call.app_references or ())
    encoded: list[dict[str, object]] = []
    for raw in raw_refs:
        ref = _normalize_box_reference(app_call, raw)
        index = _map_box_app_id_to_index(ref.app_id, app_call, app_refs)
        encoded.append({"i": index, "n": ref.name})
    return encoded


def _decode_box_references(value: object) -> tuple[_WireBoxReference, ...] | None:
    if value is None:
        return None
    if isinstance(value, list):
        entries: list[_WireBoxReference] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            index = int(item.get("i", 0))
            name_payload = item.get("n", b"")
            if isinstance(name_payload, bytes | bytearray | memoryview | list | tuple):
                name = bytes(name_payload)
            else:
                name = b""
            entries.append(_WireBoxReference(index=index, name=name))
        return tuple(entries) if entries else None
    return None


@dataclass(slots=True, frozen=True)
class AppCallTransactionFields:
    app_id: int = field(default=0, metadata=wire("apid"))
    on_complete: OnApplicationComplete = field(
        default=OnApplicationComplete.NoOp, metadata=enum_value("apan", OnApplicationComplete)
    )
    approval_program: bytes | None = field(default=None, metadata=wire("apap"))
    clear_state_program: bytes | None = field(default=None, metadata=wire("apsu"))
    global_state_schema: StateSchema | None = field(default=None, metadata=nested("apgs", StateSchema))
    local_state_schema: StateSchema | None = field(default=None, metadata=nested("apls", StateSchema))
    args: tuple[bytes, ...] | None = field(default=None, metadata=bytes_seq("apaa"))
    account_references: tuple[str, ...] | None = field(default=None, metadata=addr_seq("apat"))
    app_references: tuple[int, ...] | None = field(default=None, metadata=int_seq("apfa"))
    asset_references: tuple[int, ...] | None = field(default=None, metadata=int_seq("apas"))
    extra_program_pages: int | None = field(default=None, metadata=wire("apep"))
    box_references: tuple[BoxReference, ...] | None = field(
        default=None,
        metadata=wire(
            "apbx",
            encode=_encode_box_references,
            decode=_decode_box_references,
            pass_obj=True,
        ),
    )

    def __post_init__(self) -> None:
        if not self.box_references:
            return
        normalized = tuple(_normalize_box_reference(self, item) for item in _coerce_box_sequence(self.box_references))
        object.__setattr__(self, "box_references", normalized or None)
