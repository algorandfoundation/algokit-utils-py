import builtins
import sys
import types
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import TypeVar, Union, cast, get_args, get_origin, get_type_hints

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


DecodedValueT = TypeVar("DecodedValueT")


class EncodeError(ValueError):
    pass


class DecodeError(ValueError):
    pass


# Metadata helpers
def wire(
    alias: str,
    *,
    encode: Callable[..., object] | None = None,
    decode: Callable[..., object] | type | None = None,
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


ChildType = type[object] | Callable[[], type[object]] | None


def _expects_text_value(type_hint: object) -> bool:
    if isinstance(type_hint, type) and issubclass(type_hint, Enum):
        return True
    if type_hint is str:
        return True
    origin = get_origin(type_hint)
    if origin is None:
        return False
    if origin is str:
        return True
    if origin in (list, tuple, set, frozenset, dict):
        return False
    args = [arg for arg in get_args(type_hint) if arg is not type(None)]
    return any(_expects_text_value(arg) for arg in args)


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
    omit_empty_seq: bool = True,
    required: bool = False,
) -> dict[str, object]:
    return {
        "kind": "nested",
        "alias": alias,
        "child_cls": child_cls,
        "present_if": present_if,
        "omit_empty_seq": omit_empty_seq,
        "required": required,
    }


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
    expects_text: bool = False
    nested_required: bool = False  # For nested fields: whether they are required


class _SerdePlan:
    __slots__ = ("cls", "fields")

    def __init__(self, cls: type[object], handlers: list[_FieldHandler]) -> None:
        self.cls = cls
        self.fields = handlers


_SERDE_CACHE: dict[type[object], _SerdePlan] = {}


def _get_dataclass(typ: type) -> type | None:
    if get_origin(typ) in {Union, types.UnionType}:
        typs = set(get_args(typ))
    else:
        typs = {typ}
    typs = typs - {types.NoneType}
    try:
        (maybe_dataclass,) = typs
    except ValueError:
        return None
    if is_dataclass(maybe_dataclass):
        return cast(type, maybe_dataclass)
    else:
        return None


def _compile_plan(cls: type[object]) -> _SerdePlan:
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")
    handlers: list[_FieldHandler] = []
    # Use explicit globalns with builtins and empty localns to avoid issues with
    # dataclass fields that shadow builtin names (e.g. 'bytes', 'type').
    # When slots=True, the class namespace contains member descriptors that can
    # interfere with type hint evaluation.
    module = sys.modules.get(cls.__module__, None)
    globalns = {**vars(builtins), **(vars(module) if module else {})}
    cls_type_hints = get_type_hints(cls, globalns=globalns, localns={})
    for f in fields(cls):
        meta = dict(f.metadata or {})
        field_type = cls_type_hints[f.name]
        maybe_dataclass = _get_dataclass(field_type)
        if maybe_dataclass and not meta:
            kind = "nested"
            meta = {"child_cls": maybe_dataclass, "alias": f.name, "omit_if_none": True}
        else:
            kind = cast(str | None, meta.get("kind")) or "wire"
            if kind not in ("wire", "flatten", "nested"):
                kind = "wire"

        if kind == "wire":
            handlers.append(
                _FieldHandler(
                    name=f.name,
                    alias=cast(str | None, meta.get("alias", f.name)),
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
                    expects_text=_expects_text_value(field_type),
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
                    omit_empty_seq=meta.get("omit_empty_seq", True),
                    required=False,
                    kind=kind,
                    child_cls=cast(type[object] | None, meta.get("child_cls")),
                    nested_alias=cast(str | None, meta.get("alias")),
                    present_if=cast(Callable[[Mapping[str, object]], bool] | None, meta.get("present_if")),
                    nested_required=bool(meta.get("required", False)),
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


# Cache for default instances to avoid repeated construction
_DEFAULT_INSTANCE_CACHE: dict[type[object], object] = {}


def _construct_default_instance(cls: type[object]) -> object:
    """Construct a default instance of a dataclass with all required fields set to defaults.

    This mirrors TypeScript's ObjectModelCodec.defaultValue() behavior:
    - Required primitive fields get type-appropriate defaults (0, "", False, b"", etc.)
    - Required nested object fields get recursively constructed default instances
    - Optional fields are not set (they use their dataclass defaults, typically None)

    The result is cached for performance.
    """
    if cls in _DEFAULT_INSTANCE_CACHE:
        return _DEFAULT_INSTANCE_CACHE[cls]

    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")

    plan = _plan_for(cls)
    kwargs: dict[str, object] = {}

    for h in plan.fields:
        if h.kind == "wire":
            # For wire fields, check if it has a default in the dataclass
            # If not, we need to provide a default value for required primitives
            # The dataclass defaults should already handle this via generator
            pass
        elif h.kind == "nested" and h.nested_required:
            # Required nested fields need default instances
            child_cls = _resolve_child_cls(h)
            if child_cls is not None:
                kwargs[h.name] = _construct_default_instance(child_cls)
        # flatten and optional nested fields are not populated

    # Create instance - dataclass defaults will fill in primitive defaults
    try:
        instance = cls(**kwargs)
    except TypeError as exc:
        raise DecodeError(f"Failed to construct default instance of {cls.__name__}: {exc}") from exc

    _DEFAULT_INSTANCE_CACHE[cls] = instance
    return instance


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
    if not (nested_payload := to_wire(value)) and h.omit_empty_seq:
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
    # For flattened fields, recursively collect wire aliases from child classes
    for h in plan.fields:
        if h.kind == "flatten":
            child_cls = _resolve_child_cls(h)
            if child_cls is not None:
                aliases.update(_wire_aliases_for(child_cls))
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
    value = raw
    needs_text = bool(
        h.expects_text and (h.decode_fn is None or (isinstance(h.decode_fn, type) and issubclass(h.decode_fn, Enum)))
    )
    if needs_text and isinstance(value, bytes | bytearray | memoryview):
        raw_bytes = bytes(value)
        try:
            value = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Some Algorand fields legitimately carry printable data inside binary slots.
            value = raw_bytes
    kwargs[h.name] = _decode_with_hint(value, h.decode_fn)


def _decode_nested_field(kwargs: dict[str, object], h: _FieldHandler, payload: Mapping[str, object]) -> None:
    child_cls = _resolve_child_cls(h)
    if child_cls is None or h.nested_alias is None:
        kwargs[h.name] = None
        return
    if isinstance(raw_nested := payload.get(h.nested_alias), Mapping):
        kwargs[h.name] = from_wire(child_cls, raw_nested)
        return
    # Field is missing or not a Mapping - check if it's required
    if h.nested_required:
        # Required nested fields get a default instance (mirrors TS ObjectModelCodec.defaultValue())
        kwargs[h.name] = _construct_default_instance(child_cls)
        return
    if not h.omit_if_none:
        kwargs[h.name] = None


def _decode_flatten_field(kwargs: dict[str, object], h: _FieldHandler, payload: Mapping[str, object]) -> None:
    child_cls = _resolve_child_cls(h)
    if child_cls is None:
        kwargs[h.name] = None
        return
    alias_set = _wire_aliases_for(child_cls)
    has_any = any(_has_path(payload, k) for k in alias_set)
    # If present_if is provided, it takes precedence over the wire alias check.
    # This is important for transaction types where the same wire keys (e.g., 'amt', 'rcv')
    # could be present but the type field indicates a different transaction type.
    if h.present_if is not None:
        if not h.present_if(payload):
            kwargs[h.name] = None
            return
    elif not has_any:
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


def from_wire(cls: type[DecodedValueT], payload: Mapping[str, object]) -> DecodedValueT:
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
        return cast(DecodedValueT, plan.cls(**kwargs))
    except TypeError as exc:
        raise DecodeError(f"Failed to construct {plan.cls.__name__}: {exc}") from exc


def addr(alias: str, *, omit_if_none: bool = True) -> dict[str, object]:
    """Typed helper for address fields (str <-> bytes)."""
    from algokit_common.constants import ZERO_ADDRESS

    def _encode(v: object) -> bytes | None:
        addr_str = cast(str, v)
        # Treat ZERO_ADDRESS as default (omit from output)
        if addr_str == ZERO_ADDRESS:
            return None
        return public_key_from_address(addr_str)

    return wire(
        alias,
        encode=_encode,
        decode=lambda v: address_from_public_key(cast(bytes, v)),
        omit_if_none=omit_if_none,
    )


E = TypeVar("E", bound=Enum)


def enum_value(alias: str, enum_type: type[E], *, fallback: E | None = None) -> dict[str, object]:
    """Typed helper for Enum fields that serialize via their .value.

    Args:
        alias: The wire format key name
        enum_type: The Enum class to encode/decode
        fallback: Optional fallback value to use when decoding an unknown value.
                  If not provided, decoding unknown values will raise DecodeError.
                  This is useful for forward-compatibility when new enum values may
                  be added in the future (e.g., new transaction types).
    """

    def _decode(value: object) -> E:
        # Normalize bytes to str (msgpack may return string values as bytes)
        if isinstance(value, bytes | bytearray | memoryview):
            value = bytes(value).decode("utf-8")
        try:
            return enum_type(value)
        except ValueError:
            if fallback is not None:
                return fallback
            raise

    return wire(alias, encode=lambda e: e.value if isinstance(e, enum_type) else e, decode=_decode)


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
