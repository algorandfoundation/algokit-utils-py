from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import TypeVar, cast

from algokit_common import address_from_public_key, public_key_from_address

from algokit_common.serde._primitives import (
    decode_int_like,
    encode_bool,
    encode_int,
    omit_defaults_and_sort,
    sort_msgpack_value,
)

__all__ = [
    "DecodeError",
    "EncodeError",
    "addr",
    "addr_seq",
    "bytes_seq",
    "enum_value",
    "flatten",
    "from_wire",
    "int_seq",
    "nested",
    "sort_msgpack_value",
    "to_wire",
    "to_wire_canonical",
    "wire",
]


T = TypeVar("T")


class EncodeError(ValueError):
    pass


class DecodeError(ValueError):
    pass


# Metadata helpers
def wire(
    alias: str,
    *,
    encode: Callable[..., object] | None = None,
    decode: Callable[[object], object] | type | None = None,
    omit_if_none: bool = True,
    keep_zero: bool = False,
    keep_false: bool = False,
    omit_empty_seq: bool = True,
    required: bool = False,
    pass_obj: bool = False,
) -> dict[str, object]:
    return {
        "kind": "wire",
        "alias": alias,
        "encode": encode,
        "decode": decode,
        "omit_if_none": omit_if_none,
        "keep_zero": keep_zero,
        "keep_false": keep_false,
        "omit_empty_seq": omit_empty_seq,
        "required": required,
        "pass_obj": pass_obj,
    }


def flatten(
    child_cls: ChildType,
    *,
    present_if: Callable[[Mapping[str, object]], bool] | None = None,
) -> dict[str, object]:
    return {"kind": "flatten", "child_cls": child_cls, "present_if": present_if}


def nested(
    alias: str,
    child_cls: ChildType,
    *,
    present_if: Callable[[Mapping[str, object]], bool] | None = None,
) -> dict[str, object]:
    return {"kind": "nested", "alias": alias, "child_cls": child_cls, "present_if": present_if}


ChildType = type[object] | Callable[[], type[object]] | None


@dataclass(slots=True)
class _FieldHandler:
    name: str
    alias: str | None
    encode_fn: Callable[..., object] | None
    decode_fn: Callable[[object], object] | type | None
    omit_if_none: bool
    keep_zero: bool
    keep_false: bool
    omit_empty_seq: bool
    required: bool
    kind: str
    child_cls: ChildType
    nested_alias: str | None
    present_if: Callable[[Mapping[str, object]], bool] | None = None
    pass_obj: bool = False


class _SerdePlan:
    __slots__ = ("cls", "fields")

    def __init__(self, cls: type[object], handlers: list[_FieldHandler]) -> None:
        self.cls = cls
        self.fields = handlers


_SERDE_CACHE: dict[type[object], _SerdePlan] = {}


def _compile_plan(cls: type[object]) -> _SerdePlan:
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")
    handlers: list[_FieldHandler] = []
    for f in fields(cls):
        meta = dict(f.metadata or {})
        kind = cast(str | None, meta.get("kind")) or "wire"
        if kind not in ("wire", "flatten", "nested"):
            kind = "wire"

        if kind == "wire":
            handlers.append(
                _FieldHandler(
                    name=f.name,
                    alias=cast(str | None, meta.get("alias")),
                    encode_fn=cast(Callable[..., object] | None, meta.get("encode")),
                    decode_fn=cast(Callable[[object], object] | type | None, meta.get("decode")),
                    omit_if_none=bool(meta.get("omit_if_none", True)),
                    keep_zero=bool(meta.get("keep_zero", False)),
                    keep_false=bool(meta.get("keep_false", False)),
                    omit_empty_seq=bool(meta.get("omit_empty_seq", True)),
                    required=bool(meta.get("required", False)),
                    kind=kind,
                    child_cls=None,
                    nested_alias=None,
                    pass_obj=bool(meta.get("pass_obj", False)),
                )
            )
        elif kind == "nested":
            handlers.append(
                _FieldHandler(
                    name=f.name,
                    alias=None,
                    encode_fn=None,
                    decode_fn=None,
                    omit_if_none=True,
                    keep_zero=False,
                    keep_false=False,
                    omit_empty_seq=True,
                    required=False,
                    kind=kind,
                    child_cls=cast(type[object] | None, meta.get("child_cls")),
                    nested_alias=cast(str | None, meta.get("alias")),
                    present_if=cast(Callable[[Mapping[str, object]], bool] | None, meta.get("present_if")),
                )
            )
        else:  # flatten
            handlers.append(
                _FieldHandler(
                    name=f.name,
                    alias=None,
                    encode_fn=None,
                    decode_fn=None,
                    omit_if_none=True,
                    keep_zero=False,
                    keep_false=False,
                    omit_empty_seq=True,
                    required=False,
                    kind=kind,
                    child_cls=cast(type[object] | None, meta.get("child_cls")),
                    nested_alias=None,
                    present_if=cast(Callable[[Mapping[str, object]], bool] | None, meta.get("present_if")),
                )
            )

    plan = _SerdePlan(cls, handlers)
    _SERDE_CACHE[cls] = plan
    return plan


def _plan_for(cls: type[object]) -> _SerdePlan:
    return _SERDE_CACHE.get(cls) or _compile_plan(cls)


def _encode_scalar(value: object, *, keep_zero: bool, keep_false: bool) -> object | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value if keep_false else encode_bool(value)
    if isinstance(value, int):
        return encode_int(value, keep_zero=keep_zero)
    if isinstance(value, bytes | bytearray | memoryview):
        return bytes(value) if isinstance(value, bytearray | memoryview) else value
    return value


def _resolve_child_cls(h: _FieldHandler) -> type[object] | None:
    child = h.child_cls
    if child is None:
        return None
    if isinstance(child, type):
        return child
    return child()


def _encode_nested_field(out: dict[str, object], obj: object, h: _FieldHandler) -> None:
    if (value := getattr(obj, h.name)) is None:
        return
    if not (nested_payload := to_wire(value)):
        return
    if h.nested_alias is None:
        raise EncodeError(f"Missing nested alias for field {h.name!r}")
    out[h.nested_alias] = nested_payload


def _encode_flatten_field(out: dict[str, object], obj: object, h: _FieldHandler) -> None:
    if (value := getattr(obj, h.name)) is None:
        return
    if child_payload := to_wire(value):
        out.update(child_payload)


def _encode_wire_field(out: dict[str, object], obj: object, h: _FieldHandler) -> None:
    if not h.alias:
        return
    value = getattr(obj, h.name)
    if value is None:
        if h.required:
            raise EncodeError(f"Field {h.name!r} is required but None")
        if h.omit_if_none:
            return
        _set_path(out, h.alias, None)
        return

    if h.encode_fn is not None:
        encoded = h.encode_fn(obj, value) if h.pass_obj else h.encode_fn(value)
    else:
        encoded = _encode_scalar(value, keep_zero=h.keep_zero, keep_false=h.keep_false)

    if h.omit_empty_seq and isinstance(encoded, list | tuple) and not encoded:
        return
    if encoded is None and h.omit_if_none:
        return
    _set_path(out, h.alias, encoded)


def to_wire(obj: object) -> dict[str, object]:
    """Encode a dataclass instance to a wire-ready dict using field metadata."""
    plan = _plan_for(obj.__class__)
    out: dict[str, object] = {}
    for h in plan.fields:
        if h.kind == "nested":
            _encode_nested_field(out, obj, h)
        elif h.kind == "flatten":
            _encode_flatten_field(out, obj, h)
        elif h.kind == "wire":
            _encode_wire_field(out, obj, h)
    return out


def to_wire_canonical(obj: object) -> dict[str, object]:
    """Return canonical, ready-to-msgpack dict (omit defaults and sort keys)."""
    return cast(dict[str, object], omit_defaults_and_sort(dict(to_wire(obj))))


def _decode_with_hint(raw: object, decode_fn: Callable[[object], object] | type | None) -> object:
    if decode_fn is None:
        if isinstance(raw, bytes | bytearray):
            return bytes(raw)
        if isinstance(raw, int):
            return decode_int_like(raw)
        return raw

    if isinstance(decode_fn, type):
        try:
            return cast("Callable[[object], object]", decode_fn)(raw)
        except Exception as exc:
            raise DecodeError(f"Failed to construct {decode_fn.__name__} from {raw!r}") from exc

    return decode_fn(raw)


def _wire_aliases_for(cls: type[object]) -> frozenset[str]:
    plan = _plan_for(cls)
    aliases = {h.alias for h in plan.fields if h.kind == "wire" and h.alias}
    aliases.update(h.nested_alias for h in plan.fields if h.kind == "nested" and h.nested_alias)
    return frozenset(aliases)


def _decode_wire_field(kwargs: dict[str, object], h: _FieldHandler, payload: Mapping[str, object]) -> None:
    if not (alias := h.alias):
        return
    if not _has_path(payload, alias):
        return
    if (raw := _get_path(payload, alias)) is None:
        if h.required:
            raise DecodeError(f"Missing required field {h.name!r} (alias {alias!r})")
        kwargs[h.name] = None
        return
    kwargs[h.name] = _decode_with_hint(raw, h.decode_fn)


def _decode_nested_field(kwargs: dict[str, object], h: _FieldHandler, payload: Mapping[str, object]) -> None:
    child_cls = _resolve_child_cls(h)
    if child_cls is None or h.nested_alias is None:
        kwargs[h.name] = None
        return
    if isinstance(raw_nested := payload.get(h.nested_alias), Mapping):
        kwargs[h.name] = from_wire(child_cls, raw_nested)
        return
    kwargs[h.name] = None


def _decode_flatten_field(kwargs: dict[str, object], h: _FieldHandler, payload: Mapping[str, object]) -> None:
    child_cls = _resolve_child_cls(h)
    if child_cls is None:
        kwargs[h.name] = None
        return
    alias_set = _wire_aliases_for(child_cls)
    has_any = any(_has_path(payload, k) for k in alias_set)
    if not has_any and h.present_if is not None:
        has_any = h.present_if(payload)
    if not has_any:
        kwargs[h.name] = None
        return
    sub: dict[str, object] = {}
    for key in alias_set:
        if _has_path(payload, key):
            _set_path(sub, key, _get_path(payload, key))
    kwargs[h.name] = from_wire(child_cls, sub)


def _set_path(target: dict[str, object], path: str, value: object) -> None:
    if "." not in path:
        target[path] = value
        return
    parts = path.split(".")
    cur = target
    for key in parts[:-1]:
        if not isinstance(nxt := cur.get(key), dict):
            nxt = {}
            cur[key] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _get_path(source: Mapping[str, object], path: str) -> object | None:
    if "." not in path:
        return source.get(path)
    cur: object = source
    for key in path.split("."):
        if not isinstance(cur, Mapping) or (cur := cur.get(key)) is None:
            return None
    return cur


def _has_path(source: Mapping[str, object], path: str) -> bool:
    if "." not in path:
        return path in source
    cur: object = source
    for key in path.split("."):
        if not isinstance(cur, Mapping) or key not in cur:
            return False
        cur = cur[key]
    return True


def from_wire(cls: type[T], payload: Mapping[str, object]) -> T:
    """Decode a wire dict into a dataclass instance using field metadata."""
    plan = _plan_for(cls)
    kwargs: dict[str, object] = {}
    for h in plan.fields:
        if h.kind == "wire":
            _decode_wire_field(kwargs, h, payload)
        elif h.kind == "nested":
            _decode_nested_field(kwargs, h, payload)
        elif h.kind == "flatten":
            _decode_flatten_field(kwargs, h, payload)
    try:
        return cast(T, plan.cls(**kwargs))
    except TypeError as exc:
        raise DecodeError(f"Failed to construct {plan.cls.__name__}: {exc}") from exc


def addr(alias: str, *, omit_if_none: bool = True) -> dict[str, object]:
    """Typed helper for address fields (str <-> bytes)."""
    return wire(
        alias,
        encode=lambda v: public_key_from_address(cast(str, v)),
        decode=lambda v: address_from_public_key(cast(bytes, v)),
        omit_if_none=omit_if_none,
    )


def enum_value(alias: str, enum_type: type[Enum]) -> dict[str, object]:
    """Typed helper for Enum fields that serialize via their .value."""
    return wire(alias, encode=lambda e: e.value if isinstance(e, enum_type) else e, decode=enum_type)


def bytes_seq(alias: str, *, omit_if_none: bool = True) -> dict[str, object]:
    def _enc(value: object) -> object:
        if value is None or not isinstance(value, tuple | list):
            return None
        out = [bytes(item) for item in value if isinstance(item, bytes | bytearray | memoryview)]
        return out or None

    def _dec(value: object) -> object:
        if not isinstance(value, list):
            return value
        return tuple(bytes(item) for item in value if isinstance(item, bytes | bytearray | memoryview))

    return wire(alias, encode=_enc, decode=_dec, omit_if_none=omit_if_none)


def int_seq(alias: str, *, omit_if_none: bool = True) -> dict[str, object]:
    def _enc(value: object) -> object:
        if value is None or not isinstance(value, tuple | list):
            return None
        out = [int(item) for item in value if isinstance(item, int)]
        return out or None

    def _dec(value: object) -> object:
        if not isinstance(value, list):
            return value
        return tuple(int(item) for item in value if isinstance(item, int))

    return wire(alias, encode=_enc, decode=_dec, omit_if_none=omit_if_none)


def addr_seq(alias: str, *, omit_if_none: bool = True) -> dict[str, object]:
    def _enc(value: object) -> object:
        if value is None or not isinstance(value, tuple | list):
            return None
        out = [public_key_from_address(cast(str, item)) for item in value]
        return out or None

    def _dec(value: object) -> object:
        if not isinstance(value, list):
            return value
        return tuple(address_from_public_key(bytes(item)) for item in value if isinstance(item, bytes | bytearray))

    return wire(alias, encode=_enc, decode=_dec, omit_if_none=omit_if_none)
