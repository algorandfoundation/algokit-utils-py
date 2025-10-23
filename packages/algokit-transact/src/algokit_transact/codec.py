from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from typing import TypedDict

import msgpack

from .address import address_from_public_key, public_key_from_address
from .constants import TRANSACTION_DOMAIN_SEPARATOR
from .types import (
    AppCallFields,
    AssetConfigFields,
    AssetTransferFields,
    OnApplicationComplete,
    PaymentFields,
    StateSchema,
    Transaction,
    TransactionType,
)
from .validation import validate_transaction


class _StateSchemaDto(TypedDict, total=False):
    nui: int
    nbs: int


class _AssetParamsDto(TypedDict, total=False):
    t: int | None
    dc: int | None
    df: bool | None
    un: str | None
    an: str | None
    au: str | None
    am: bytes | None
    m: bytes | None
    f: bytes | None
    c: bytes | None
    r: bytes | None


class _TransactionDto(TypedDict, total=False):
    # common
    type: str
    snd: bytes
    fv: int
    lv: int
    gen: str
    gh: bytes
    fee: int
    note: bytes
    lx: bytes
    rekey: bytes
    grp: bytes

    # payment
    amt: int
    rcv: bytes
    close: bytes

    # axfer
    xaid: int
    aamt: int
    arcv: bytes
    aclose: bytes
    asnd: bytes

    # acfg
    caid: int
    apar: _AssetParamsDto

    # afrz
    faid: int
    fadd: bytes
    afrz: bool

    # appl
    apid: int
    apan: int
    apap: bytes
    apsu: bytes
    apgs: _StateSchemaDto
    apls: _StateSchemaDto
    apaa: list[bytes]
    apat: list[bytes]
    apfa: list[int]
    apas: list[int]
    apep: int


def _to_type_str(t: TransactionType) -> str:
    return t.value


def _from_type_str(s: str) -> TransactionType:
    return TransactionType(s)


def _encode_address(addr: str | None) -> bytes | None:
    if addr is None:
        return None
    return public_key_from_address(addr)


def _decode_address(pk: bytes | None) -> str | None:
    if pk is None:
        return None
    return address_from_public_key(pk)


def _encode_bytes(b: bytes | None) -> bytes | None:
    return b if b not in (None, b"") else None


def _encode_int(n: int | None) -> int | None:
    return None if n in (None, 0) else n


def _encode_bool(v: bool | None) -> bool | None:
    return None if v in (None, False) else v


def to_transaction_dto(tx: Transaction) -> _TransactionDto:
    dto: _TransactionDto = {
        "type": _to_type_str(tx.transaction_type),
        "snd": _encode_address(tx.sender),
        "fv": _encode_int(tx.first_valid),
        "lv": _encode_int(tx.last_valid),
        "gen": tx.genesis_id or None,
        "gh": _encode_bytes(tx.genesis_hash),
        "fee": _encode_int(tx.fee),
        "note": _encode_bytes(tx.note),
        "lx": _encode_bytes(tx.lease),
        "rekey": _encode_address(tx.rekey_to),
        "grp": _encode_bytes(tx.group),
    }

    pf = tx.payment
    if pf is not None:
        dto.update(
            {
                "amt": _encode_int(pf.amount),
                "rcv": _encode_address(pf.receiver),
                "close": _encode_address(pf.close_remainder_to),
            }
        )

    xf = tx.asset_transfer
    if xf is not None:
        dto.update(
            {
                "xaid": _encode_int(xf.asset_id),
                "aamt": _encode_int(xf.amount),
                "arcv": _encode_address(xf.receiver),
                "aclose": _encode_address(xf.close_remainder_to),
                "asnd": _encode_address(xf.asset_sender),
            }
        )

    cf = tx.asset_config
    if cf is not None:
        apar: _AssetParamsDto = {
            "t": _encode_int(cf.total),
            "dc": _encode_int(cf.decimals),
            "df": _encode_bool(cf.default_frozen),
            "un": cf.unit_name or None,
            "an": cf.asset_name or None,
            "au": cf.url or None,
            "am": _encode_bytes(cf.metadata_hash),
            "m": _encode_address(cf.manager),
            "f": _encode_address(cf.freeze),
            "c": _encode_address(cf.clawback),
            "r": _encode_address(cf.reserve),
        }
        dto.update(
            {
                "caid": _encode_int(cf.asset_id),
                "apar": apar,
            }
        )

    ff = tx.asset_freeze
    if ff is not None:
        dto.update(
            {
                "faid": _encode_int(ff.asset_id),
                "fadd": _encode_address(ff.freeze_target),
                "afrz": _encode_bool(ff.frozen),
            }
        )

    af = tx.app_call
    if af is not None:
        dto.update(
            {
                "apid": _encode_int(af.app_id),
                "apan": af.on_complete.value,
                "apap": _encode_bytes(af.approval_program),
                "apsu": _encode_bytes(af.clear_state_program),
                "apgs": (
                    {"nui": af.global_state_schema.num_uints, "nbs": af.global_state_schema.num_byte_slices}
                    if af.global_state_schema
                    else None
                ),
                "apls": (
                    {"nui": af.local_state_schema.num_uints, "nbs": af.local_state_schema.num_byte_slices}
                    if af.local_state_schema
                    else None
                ),
                "apaa": list(af.args) if af.args is not None else None,
                "apat": [public_key_from_address(a) for a in af.account_references] if af.account_references else None,
                "apfa": list(af.app_references) if af.app_references else None,
                "apas": list(af.asset_references) if af.asset_references else None,
                "apep": _encode_int(af.extra_program_pages),
            }
        )

    return dto


def _omit_defaults_and_sort(value: object) -> object:
    if isinstance(value, dict):
        filtered: dict[str, object] = {}
        for k, v in value.items():
            vv = _omit_defaults_and_sort(v)
            if _is_default_like(vv):
                continue
            filtered[k] = vv
        # Convert to plain dict to keep msgpack happy, preserving sorted key order
        return dict(OrderedDict(sorted(filtered.items())))
    if isinstance(value, list | tuple):
        return [_omit_defaults_and_sort(v) for v in value]
    return value


def _is_default_like(value: object) -> bool:
    if value is None:
        return True
    # primitives
    if isinstance(value, int) and value == 0:
        return True
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (bytes, bytearray)) and len(value) == 0:
        return True
    # containers
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict):
        # omit-empty-object
        return all(_is_default_like(v) for v in value.values())
    return False


def encode_transaction_raw(tx: Transaction) -> bytes:
    validate_transaction(tx)
    dto = to_transaction_dto(tx)
    canonical = _omit_defaults_and_sort(dto)
    return msgpack.packb(canonical, use_bin_type=True, strict_types=True)


def encode_transaction(tx: Transaction) -> bytes:
    raw = encode_transaction_raw(tx)
    prefix = TRANSACTION_DOMAIN_SEPARATOR.encode()
    return prefix + raw


def from_transaction_dto(dto: Mapping[str, object]) -> Transaction:
    ttype = _from_type_str(dto["type"])  # type: ignore[index]

    def get_bytes(key: str) -> bytes | None:
        v = dto.get(key)
        return v if isinstance(v, bytes | bytearray) else None

    def get_str_addr(key: str) -> str | None:
        v = get_bytes(key)
        return _decode_address(v)

    def get_int(key: str) -> int | None:
        v = dto.get(key)
        if isinstance(v, bool):
            return int(v)
        return int(v) if isinstance(v, int) else None

    common = {
        "transaction_type": ttype,
        "sender": get_str_addr("snd") or "",
        "first_valid": get_int("fv") or 0,
        "last_valid": get_int("lv") or 0,
        "fee": get_int("fee"),
        "genesis_id": (dto.get("gen") if isinstance(dto.get("gen"), str) else None),
        "genesis_hash": get_bytes("gh"),
        "note": get_bytes("note"),
        "lease": get_bytes("lx"),
        "rekey_to": get_str_addr("rekey"),
        "group": get_bytes("grp"),
    }

    payment: PaymentFields | None = None
    if "amt" in dto or "rcv" in dto or "close" in dto:
        payment = PaymentFields(
            amount=get_int("amt") or 0,
            receiver=get_str_addr("rcv") or "",
            close_remainder_to=get_str_addr("close"),
        )

    asset_transfer: AssetTransferFields | None = None
    if any(k in dto for k in ("xaid", "aamt", "arcv", "aclose", "asnd")):
        asset_transfer = AssetTransferFields(
            asset_id=get_int("xaid") or 0,
            amount=get_int("aamt") or 0,
            receiver=get_str_addr("arcv") or "",
            close_remainder_to=get_str_addr("aclose"),
            asset_sender=get_str_addr("asnd"),
        )

    asset_config: AssetConfigFields | None = None
    if "caid" in dto or "apar" in dto:
        apar = dto.get("apar")
        params: dict[str, object] = apar if isinstance(apar, Mapping) else {}
        asset_config = AssetConfigFields(
            asset_id=get_int("caid") or 0,
            total=int(params.get("t")) if isinstance(params.get("t"), int) else None,
            decimals=int(params.get("dc")) if isinstance(params.get("dc"), int) else None,
            default_frozen=bool(params.get("df")) if isinstance(params.get("df"), bool) else None,
            unit_name=params.get("un") if isinstance(params.get("un"), str) else None,
            asset_name=params.get("an") if isinstance(params.get("an"), str) else None,
            url=params.get("au") if isinstance(params.get("au"), str) else None,
            metadata_hash=params.get("am") if isinstance(params.get("am"), bytes | bytearray) else None,
            manager=(
                address_from_public_key(params.get("m")) if isinstance(params.get("m"), bytes | bytearray) else None
            ),
            reserve=(
                address_from_public_key(params.get("r")) if isinstance(params.get("r"), bytes | bytearray) else None
            ),
            freeze=(
                address_from_public_key(params.get("f")) if isinstance(params.get("f"), bytes | bytearray) else None
            ),
            clawback=(
                address_from_public_key(params.get("c")) if isinstance(params.get("c"), bytes | bytearray) else None
            ),
        )

    app_call: AppCallFields | None = None
    if any(k in dto for k in ("apid", "apan", "apap", "apsu", "apgs", "apls", "apaa", "apat", "apfa", "apas", "apep")):
        apgs = dto.get("apgs")
        apls = dto.get("apls")
        args_list = dto.get("apaa") if isinstance(dto.get("apaa"), list) else None
        apat_list = dto.get("apat") if isinstance(dto.get("apat"), list) else None
        app_call = AppCallFields(
            app_id=get_int("apid") or 0,
            on_complete=OnApplicationComplete(dto.get("apan") or 0),
            approval_program=get_bytes("apap"),
            clear_state_program=get_bytes("apsu"),
            global_state_schema=(
                None
                if not isinstance(apgs, Mapping)
                else StateSchema(
                    num_uints=int(apgs.get("nui", 0)),
                    num_byte_slices=int(apgs.get("nbs", 0)),
                )
            ),
            local_state_schema=(
                None
                if not isinstance(apls, Mapping)
                else StateSchema(
                    num_uints=int(apls.get("nui", 0)),
                    num_byte_slices=int(apls.get("nbs", 0)),
                )
            ),
            args=tuple(args_list) if args_list else None,
            account_references=(tuple(address_from_public_key(a) for a in apat_list) if apat_list else None),
            app_references=(tuple(int(x) for x in dto.get("apfa", [])) if isinstance(dto.get("apfa"), list) else None),
            asset_references=(
                tuple(int(x) for x in dto.get("apas", [])) if isinstance(dto.get("apas"), list) else None
            ),
            extra_program_pages=get_int("apep"),
        )

    return Transaction(
        **common,
        payment=payment,
        asset_transfer=asset_transfer,
        asset_config=asset_config,
        app_call=app_call,
    )


def decode_transaction(encoded: bytes) -> Transaction:
    if not encoded:
        raise ValueError("attempted to decode 0 bytes")
    prefix = TRANSACTION_DOMAIN_SEPARATOR.encode()
    if encoded[: len(prefix)] == prefix:
        payload = encoded[len(prefix) :]
    else:
        payload = encoded
    dto = msgpack.unpackb(payload, raw=False)
    if not isinstance(dto, dict):
        raise ValueError("decoded msgpack is not a dict")
    return from_transaction_dto(dto)
