from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, cast

from algokit_common.address import address_from_public_key
from algokit_common.constants import ZERO_ADDRESS
from algokit_transact.codec.serde import (
    DecodeError,
    EncodeError,
    addr,
    addr_seq,
    bytes_seq,
    enum_value,
    int_seq,
    nested,
    to_wire,
    wire,
)
from algokit_transact.models.common import OnApplicationComplete, StateSchema


def _decode_address_field(value: object) -> str:
    """Decode address from wire format (can be bytes or string)"""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        # The API returns address as UTF-8 encoded string, not public key bytes
        return value.decode("utf-8")
    raise DecodeError(f"Invalid address format: {type(value)}")


@dataclass(slots=True, frozen=True)
class BoxReference:
    app_id: int = field(default=0, metadata=wire("app"))
    name: bytes = field(default=b"", metadata=wire("name"))


@dataclass(slots=True, frozen=True)
class HoldingReference:
    asset_id: int = field(metadata=wire("asset"))
    address: str = field(metadata=wire("account", decode=_decode_address_field))


@dataclass(slots=True, frozen=True)
class LocalsReference:
    app_id: int = field(metadata=wire("app"))
    address: str = field(metadata=wire("account", decode=_decode_address_field))


@dataclass(slots=True, frozen=True)
class ResourceReference:
    address: str | None = None
    app_id: int | None = None
    asset_id: int | None = None
    holding: HoldingReference | None = None
    locals: LocalsReference | None = None
    box: BoxReference | None = None


@dataclass(slots=True, frozen=True)
class _WireBoxReference:
    index: int
    name: bytes


@dataclass(slots=True, frozen=True)
class _AddressAccessEntry:
    address: str = field(metadata=addr("d", omit_if_none=False))


ByteLike = bytes | bytearray | memoryview


def _coerce_bytes(payload: object) -> bytes | None:
    if isinstance(payload, ByteLike):
        return bytes(payload)
    if isinstance(payload, Sequence) and not isinstance(payload, str | bytes | bytearray | memoryview):
        ints: list[int] = []
        for part in payload:
            if isinstance(part, bool):
                ints.append(int(part))
                continue
            if isinstance(part, int):
                ints.append(part)
                continue
            return None
        try:
            return bytes(ints)
        except ValueError:
            return None
    return None


def _require_bytes(payload: object | None, context: str) -> bytes:
    data = _coerce_bytes(payload) if payload is not None else None
    if data is None:
        raise EncodeError(f"{context} must be bytes-like")
    return data


def _encode_box_references(
    app_call: "AppCallTransactionFields",
    value: object,
) -> list[dict[str, object]] | None:
    if value is None:
        return None
    if not isinstance(value, Iterable):
        raise EncodeError("Box references must be iterable")
    raw_refs = _coerce_box_sequence(cast(Iterable[BoxReference | _WireBoxReference], value))
    if not raw_refs:
        return None

    app_refs = app_call.app_references or []
    encoded: list[dict[str, object]] = []
    for raw in raw_refs:
        ref = _normalize_box_reference(app_call, raw)
        index = _map_box_app_id_to_index(ref.app_id, app_call, app_refs)
        encoded.append({"i": index, "n": ref.name})
    return encoded


def _decode_box_references(value: object) -> list[_WireBoxReference] | None:
    if value is None:
        return None
    if isinstance(value, list):
        entries: list[_WireBoxReference] = []
        for item in value:
            if not isinstance(item, Mapping):
                continue
            index = int(item.get("i", 0))
            name_payload = item.get("n", b"")
            name = _coerce_bytes(name_payload) or b""
            entries.append(_WireBoxReference(index=index, name=name))
        return list(entries) if entries else None
    return None


def _encode_access_references(
    app_call: "AppCallTransactionFields",
    value: object,
) -> list[dict[str, object]] | None:
    if value is None:
        return None
    if not isinstance(value, Iterable):
        raise EncodeError("Access references must be iterable")
    raw_refs = _coerce_resource_sequence(cast(Iterable[ResourceReference], value))
    if not raw_refs:
        return None

    builder = _AccessListBuilder(app_call)
    for ref in (_normalize_resource_reference(item) for item in raw_refs):
        builder.add(ref)

    return builder.entries or None


def _decode_access_references(value: object) -> list[ResourceReference] | None:  # noqa: C901, PLR0912, PLR0915
    if value is None:
        return None
    if not isinstance(value, list):
        return None

    result: list[ResourceReference] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        if "d" in item:
            address_raw = item.get("d")
            address_bytes = _coerce_bytes(address_raw)
            if address_bytes is None:
                continue
            result.append(ResourceReference(address=address_from_public_key(address_bytes)))
            continue
        if "s" in item:
            asset_raw = item.get("s")
            if not isinstance(asset_raw, int):
                continue
            result.append(ResourceReference(asset_id=asset_raw))
            continue
        if "p" in item:
            app_raw = item.get("p")
            if not isinstance(app_raw, int):
                continue
            result.append(ResourceReference(app_id=app_raw))
            continue
        if "h" in item:
            holding_payload = item.get("h")
            if not isinstance(holding_payload, Mapping):
                continue
            asset_index_raw = holding_payload.get("s")
            if not isinstance(asset_index_raw, int):
                raise DecodeError("Holding missing asset index")
            asset_index = asset_index_raw
            if asset_index <= 0 or asset_index > len(result):
                raise DecodeError("Holding asset index out of bounds")
            asset_entry = result[asset_index - 1]
            if asset_entry.asset_id is None:
                raise DecodeError("Holding asset index does not reference an asset")
            address_index_raw = holding_payload.get("d")
            address_index = int(address_index_raw) if isinstance(address_index_raw, int) else 0
            if address_index == 0:
                address = ZERO_ADDRESS
            else:
                if address_index > len(result):
                    raise DecodeError("Holding address index out of bounds")
                address_entry = result[address_index - 1]
                if address_entry.address is None:
                    raise DecodeError("Holding address index does not reference an address")
                address = address_entry.address
            result.append(ResourceReference(holding=HoldingReference(asset_id=asset_entry.asset_id, address=address)))
            continue
        if "l" in item:
            locals_payload = item.get("l")
            if not isinstance(locals_payload, Mapping):
                continue
            address_index_raw = locals_payload.get("d")
            address_index = int(address_index_raw) if isinstance(address_index_raw, int) else 0
            if address_index == 0:
                address = ZERO_ADDRESS
            else:
                if address_index > len(result):
                    raise DecodeError("Locals address index out of bounds")
                address_entry = result[address_index - 1]
                if address_entry.address is None:
                    raise DecodeError("Locals address index does not reference an address")
                address = address_entry.address
            app_index_raw = locals_payload.get("p")
            app_index = int(app_index_raw) if isinstance(app_index_raw, int) else 0
            if app_index == 0:
                app_id = 0
            else:
                if app_index > len(result):
                    raise DecodeError("Locals app index out of bounds")
                app_entry = result[app_index - 1]
                if app_entry.app_id is None:
                    raise DecodeError("Locals app index does not reference an app")
                app_id = app_entry.app_id
            result.append(ResourceReference(locals=LocalsReference(app_id=app_id, address=address)))
            continue
        if "b" in item:
            box_payload = item.get("b")
            if not isinstance(box_payload, Mapping):
                continue
            name_raw = box_payload.get("n")
            name = _coerce_bytes(name_raw)
            if name is None:
                raise DecodeError("Box missing name")
            app_index_raw = box_payload.get("i")
            app_index = int(app_index_raw) if isinstance(app_index_raw, int) else 0
            if app_index == 0:
                app_id = 0
            else:
                if app_index > len(result):
                    raise DecodeError("Box app index out of bounds")
                app_entry = result[app_index - 1]
                if app_entry.app_id is None:
                    raise DecodeError("Box app index does not reference an app")
                app_id = app_entry.app_id
            result.append(ResourceReference(box=BoxReference(app_id=app_id, name=name)))

    return list(result) if result else None


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
    args: list[bytes] | None = field(default=None, metadata=bytes_seq("apaa"))
    account_references: list[str] | None = field(default=None, metadata=addr_seq("apat"))
    app_references: list[int] | None = field(default=None, metadata=int_seq("apfa"))
    asset_references: list[int] | None = field(default=None, metadata=int_seq("apas"))
    extra_program_pages: int | None = field(default=None, metadata=wire("apep"))
    reject_version: int | None = field(default=None, metadata=wire("aprv"))
    box_references: list[BoxReference] | None = field(
        default=None,
        metadata=wire(
            "apbx",
            encode=_encode_box_references,
            decode=_decode_box_references,
            pass_obj=True,
        ),
    )
    access_references: list[ResourceReference] | None = field(
        default=None,
        metadata=wire(
            "al",
            encode=_encode_access_references,
            decode=_decode_access_references,
            pass_obj=True,
        ),
    )

    def __post_init__(self) -> None:
        if self.box_references:
            normalized_boxes = [
                _normalize_box_reference(self, item) for item in _coerce_box_sequence(self.box_references)
            ]
            object.__setattr__(self, "box_references", normalized_boxes or None)
        if self.access_references:
            normalized_access = [
                _normalize_resource_reference(item) for item in _coerce_resource_sequence(self.access_references)
            ]
            object.__setattr__(self, "access_references", normalized_access or None)


def _coerce_box_sequence(
    boxes: Iterable[BoxReference | _WireBoxReference],
) -> list[BoxReference | _WireBoxReference]:
    if isinstance(boxes, list):
        return boxes
    return list(boxes)


def _coerce_resource_sequence(
    resources: Iterable[ResourceReference],
) -> list[ResourceReference]:
    if isinstance(resources, list):
        return resources
    return list(resources)


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


def _normalize_resource_reference(ref: ResourceReference) -> ResourceReference:
    if isinstance(ref, ResourceReference):
        return ref
    raise TypeError("Unsupported resource reference payload")


def _map_box_index_to_app_id(index: int, app_call: AppCallTransactionFields) -> int:
    if index == 0:
        return app_call.app_id
    app_refs = app_call.app_references or []
    pos = index - 1
    if pos < 0 or pos >= len(app_refs):
        raise DecodeError("Box reference index is out of bounds for application references")
    return app_refs[pos]


def _map_box_app_id_to_index(
    app_id: int,
    app_call: AppCallTransactionFields,
    app_refs: list[int],
) -> int:
    if app_id in (0, app_call.app_id):
        return 0
    try:
        pos = app_refs.index(app_id)
    except ValueError as exc:
        raise EncodeError("Box reference app id must exist in application references") from exc
    return pos + 1


class _AccessListBuilder:
    def __init__(self, app_call: "AppCallTransactionFields") -> None:
        self._app_call = app_call
        self._entries: list[dict[str, object]] = []

    @property
    def entries(self) -> list[dict[str, object]]:
        return self._entries

    def add(self, ref: ResourceReference) -> None:
        if self._register_direct(ref):
            return
        if self._register_holding(ref):
            return
        if self._register_locals(ref):
            return
        self._register_box(ref)

    def ensure(self, target: ResourceReference) -> int:
        if target.address:
            address_entry = to_wire(_AddressAccessEntry(address=target.address))
            encoded_address = _require_bytes(address_entry.get("d"), "Address access entry")
            return self._ensure_entry("d", encoded_address)

        if target.asset_id is not None:
            return self._ensure_entry("s", int(target.asset_id))

        if target.app_id is not None:
            return self._ensure_entry("p", int(target.app_id))

        return len(self._entries)

    def _ensure_entry(self, key: Literal["d", "s", "p"], value: bytes | int) -> int:
        for idx, entry in enumerate(self._entries):
            if entry.get(key) == value:
                return idx + 1
        self._entries.append({key: value})
        return len(self._entries)

    def _register_direct(self, ref: ResourceReference) -> bool:
        if not (ref.address or ref.asset_id is not None or ref.app_id is not None):
            return False
        self.ensure(ref)
        return True

    def _register_holding(self, ref: ResourceReference) -> bool:
        holding = ref.holding
        if holding is None:
            return False
        address_index = 0
        if holding.address and holding.address != ZERO_ADDRESS:
            address_index = self.ensure(ResourceReference(address=holding.address))
        asset_index = self.ensure(ResourceReference(asset_id=holding.asset_id))
        self._entries.append({"h": {"d": address_index, "s": asset_index}})
        return True

    def _register_locals(self, ref: ResourceReference) -> bool:
        locals_ref = ref.locals
        if locals_ref is None:
            return False
        address_index = 0
        if locals_ref.address and locals_ref.address != ZERO_ADDRESS:
            address_index = self.ensure(ResourceReference(address=locals_ref.address))
        app_index = 0
        if locals_ref.app_id and locals_ref.app_id != self._app_call.app_id:
            app_index = self.ensure(ResourceReference(app_id=locals_ref.app_id))
        self._entries.append({"l": {"d": address_index, "p": app_index}})
        return True

    def _register_box(self, ref: ResourceReference) -> bool:
        box_ref = ref.box
        if box_ref is None:
            return False
        app_index = 0
        if box_ref.app_id not in (0, self._app_call.app_id):
            app_index = self.ensure(ResourceReference(app_id=box_ref.app_id))
        self._entries.append({"b": {"i": app_index, "n": box_ref.name}})
        return True
