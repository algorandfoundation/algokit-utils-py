from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping, MutableMapping
from typing import cast

from .address import address_from_public_key, public_key_from_address
from .constants import TRANSACTION_DOMAIN_SEPARATOR
from .dto import (
    AssetParamsDto,
    FalconSignatureStructDto,
    HashFactoryDto,
    HeartbeatDto,
    HeartbeatProofDto,
    MerkleArrayProofDto,
    MerkleSignatureVerifierDto,
    ParticipantDto,
    RevealEntryDto,
    RevealMapDto,
    SigslotCommitDto,
    StateProofDto,
    StateProofMessageDto,
    TransactionDto,
)
from .dto_utils import set_if
from .msgpack_utils import decode_msgpack, encode_msgpack
from .types import (
    AppCallFields,
    AssetConfigFields,
    AssetFreezeFields,
    AssetTransferFields,
    FalconSignatureStruct,
    FalconVerifier,
    HashFactory,
    HeartbeatFields,
    HeartbeatProof,
    KeyRegistrationFields,
    MerkleArrayProof,
    MerkleSignatureVerifier,
    OnApplicationComplete,
    Participant,
    PaymentFields,
    Reveal,
    SigslotCommit,
    StateProof,
    StateProofFields,
    StateProofMessage,
    StateSchema,
    Transaction,
    TransactionType,
)
from .validation import validate_transaction


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


def _encode_int(n: int | None, *, keep_zero: bool = False) -> int | None:
    if n is None:
        return None
    if n == 0 and not keep_zero:
        return None
    return n


def _encode_bool(v: bool | None) -> bool | None:
    return None if v in (None, False) else v


def _encode_bytes_sequence(seq: tuple[bytes, ...] | None) -> list[bytes] | None:
    if not seq:
        return None
    return [bytes(item) for item in seq]


def _encode_int_sequence(seq: tuple[int, ...] | None) -> list[int] | None:
    if not seq:
        return None
    return [int(item) for item in seq]


def _encode_hash_factory(factory: HashFactory | None) -> HashFactoryDto | None:
    if factory is None or factory.hash_type is None:
        return None
    return {"t": factory.hash_type}


def _encode_merkle_array_proof(proof: MerkleArrayProof | None) -> MerkleArrayProofDto | None:
    if proof is None:
        return None
    dto: MerkleArrayProofDto = {}
    path = _encode_bytes_sequence(proof.path)
    if path is not None:
        dto["pth"] = path
    hash_factory = _encode_hash_factory(proof.hash_factory)
    if hash_factory is not None:
        dto["hsh"] = hash_factory
    tree_depth = _encode_int(proof.tree_depth)
    if tree_depth is not None:
        dto["td"] = tree_depth
    return dto


def _encode_participant(participant: Participant | None) -> ParticipantDto | None:
    if participant is None:
        return None
    payload: ParticipantDto = {}
    verifier = participant.verifier
    if verifier is not None:
        verifier_dto: MerkleSignatureVerifierDto = {}
        commitment = _encode_bytes(verifier.commitment)
        if commitment is not None:
            verifier_dto["cmt"] = commitment
        key_lifetime = _encode_int(verifier.key_lifetime)
        if key_lifetime is not None:
            verifier_dto["lf"] = key_lifetime
        payload["p"] = verifier_dto
    weight = _encode_int(participant.weight)
    if weight is not None:
        payload["w"] = weight
    return payload if payload else None


def _encode_falcon_signature(sig: FalconSignatureStruct | None) -> FalconSignatureStructDto | None:
    if sig is None:
        return None
    payload: FalconSignatureStructDto = {}
    signature = _encode_bytes(sig.signature)
    if signature is not None:
        payload["sig"] = signature
    index_value = _encode_int(sig.vector_commitment_index)
    if index_value is not None:
        payload["idx"] = index_value
    proof = _encode_merkle_array_proof(sig.proof)
    if proof is not None:
        payload["prf"] = proof
    verifier = sig.verifying_key
    if verifier is not None:
        vk = _encode_bytes(verifier.public_key)
        if vk is not None:
            payload["vkey"] = {"k": vk}
    return payload


def _encode_sigslot(sigslot: SigslotCommit | None) -> SigslotCommitDto | None:
    if sigslot is None:
        return None
    payload: SigslotCommitDto = {}
    signature_payload = _encode_falcon_signature(sigslot.sig)
    if signature_payload is not None:
        payload["s"] = signature_payload
    lower_sig_weight = _encode_int(sigslot.lower_sig_weight)
    if lower_sig_weight is not None:
        payload["l"] = lower_sig_weight
    return payload if payload else None


def _encode_reveals(reveals: tuple[Reveal, ...] | None) -> RevealMapDto | None:
    if not reveals:
        return None
    result: RevealMapDto = {}
    for reveal in reveals:
        position = _encode_int(reveal.position) or 0
        entry: RevealEntryDto = {}
        sigslot = _encode_sigslot(reveal.sigslot)
        if sigslot is not None:
            entry["s"] = sigslot
        participant = _encode_participant(reveal.participant)
        if participant is not None:
            entry["p"] = participant
        result[int(position)] = entry
    return result


def _encode_state_proof_proof(proof: MerkleArrayProof | None) -> MerkleArrayProofDto | None:
    return _encode_merkle_array_proof(proof)


def _decode_bytes_like(value: object | None) -> bytes | None:
    if isinstance(value, bytes | bytearray):
        return bytes(value)
    return None


def _decode_int_like(value: object | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    return None


def _decode_hash_factory(dto: object | None) -> HashFactory | None:
    if not isinstance(dto, Mapping):
        return None
    return HashFactory(hash_type=_decode_int_like(dto.get("t")))


def _decode_merkle_array_proof(dto: object | None) -> MerkleArrayProof | None:
    if not isinstance(dto, Mapping):
        return None
    path_payload = dto.get("pth")
    path: tuple[bytes, ...] | None = None
    if isinstance(path_payload, list):
        path = tuple(bytes(item) for item in path_payload if isinstance(item, bytes | bytearray))
    return MerkleArrayProof(
        path=path,
        hash_factory=_decode_hash_factory(dto.get("hsh")),
        tree_depth=_decode_int_like(dto.get("td")),
    )


def _decode_merkle_signature_verifier(dto: object | None) -> MerkleSignatureVerifier | None:
    if not isinstance(dto, Mapping):
        return None
    return MerkleSignatureVerifier(
        commitment=_decode_bytes_like(dto.get("cmt")),
        key_lifetime=_decode_int_like(dto.get("lf")),
    )


def _decode_participant(dto: object | None) -> Participant | None:
    if not isinstance(dto, Mapping):
        return None
    verifier = _decode_merkle_signature_verifier(dto.get("p"))
    return Participant(
        verifier=verifier,
        weight=_decode_int_like(dto.get("w")),
    )


def _decode_falcon_verifier(dto: object | None) -> FalconVerifier | None:
    if not isinstance(dto, Mapping):
        return None
    return FalconVerifier(public_key=_decode_bytes_like(dto.get("k")))


def _decode_falcon_signature(dto: object | None) -> FalconSignatureStruct | None:
    if not isinstance(dto, Mapping):
        return None
    return FalconSignatureStruct(
        signature=_decode_bytes_like(dto.get("sig")),
        vector_commitment_index=_decode_int_like(dto.get("idx")),
        proof=_decode_merkle_array_proof(dto.get("prf")),
        verifying_key=_decode_falcon_verifier(dto.get("vkey")),
    )


def _decode_sigslot(dto: object | None) -> SigslotCommit | None:
    if not isinstance(dto, Mapping):
        return None
    return SigslotCommit(
        sig=_decode_falcon_signature(dto.get("s")),
        lower_sig_weight=_decode_int_like(dto.get("l")),
    )


def _decode_reveals(dto: object | None) -> tuple[Reveal, ...] | None:
    if dto is None:
        return None
    reveals: list[Reveal] = []
    if isinstance(dto, Mapping):
        iterator: Iterable[tuple[object, object]] = dto.items()
    elif isinstance(dto, list):
        iterator = enumerate(dto)
    else:
        return None
    for key, value in iterator:
        if not isinstance(value, Mapping):
            continue
        position = _decode_int_like(key) if not isinstance(key, tuple) else None
        if position is None:
            position = _decode_int_like(value.get("position")) or 0
        reveals.append(
            Reveal(
                participant=_decode_participant(value.get("p")),
                sigslot=_decode_sigslot(value.get("s")),
                position=position,
            )
        )
    return tuple(reveals)


def _decode_state_proof(dto: object | None) -> StateProof | None:
    if not isinstance(dto, Mapping):
        return None
    return StateProof(
        sig_commit=_decode_bytes_like(dto.get("c")),
        signed_weight=_decode_int_like(dto.get("w")),
        sig_proofs=_decode_merkle_array_proof(dto.get("S")),
        part_proofs=_decode_merkle_array_proof(dto.get("P")),
        merkle_signature_salt_version=_decode_int_like(dto.get("v")),
        reveals=_decode_reveals(dto.get("r")),
        positions_to_reveal=tuple(int(x) for x in dto.get("pr", []) if isinstance(x, int))
        if isinstance(dto.get("pr"), list)
        else None,
    )


def _decode_state_proof_message(dto: object | None) -> StateProofMessage | None:
    if not isinstance(dto, Mapping):
        return None
    return StateProofMessage(
        block_headers_commitment=_decode_bytes_like(dto.get("b")),
        voters_commitment=_decode_bytes_like(dto.get("v")),
        ln_proven_weight=_decode_int_like(dto.get("P")),
        first_attested_round=_decode_int_like(dto.get("f")),
        last_attested_round=_decode_int_like(dto.get("l")),
    )


def _decode_heartbeat(dto: object | None) -> HeartbeatFields | None:
    if not isinstance(dto, Mapping):
        return None
    address = _decode_bytes_like(dto.get("a"))
    proof_dto = dto.get("prf")
    proof = None
    if isinstance(proof_dto, Mapping):
        proof = HeartbeatProof(
            signature=_decode_bytes_like(proof_dto.get("s")),
            public_key=_decode_bytes_like(proof_dto.get("p")),
            public_key_2=_decode_bytes_like(proof_dto.get("p2")),
            public_key_1_signature=_decode_bytes_like(proof_dto.get("p1s")),
            public_key_2_signature=_decode_bytes_like(proof_dto.get("p2s")),
        )
    return HeartbeatFields(
        address=address_from_public_key(address) if address is not None else None,
        proof=proof,
        seed=_decode_bytes_like(dto.get("sd")),
        vote_id=_decode_bytes_like(dto.get("vid")),
        key_dilution=_decode_int_like(dto.get("kd")),
    )


# Small helpers to add type-specific fields to DTO


def _add_payment_fields(dto: MutableMapping[str, object], payment_fields: PaymentFields) -> None:
    set_if(dto, "amt", _encode_int(payment_fields.amount))
    dto["rcv"] = public_key_from_address(payment_fields.receiver)
    set_if(dto, "close", _encode_address(payment_fields.close_remainder_to))


def _add_asset_transfer_fields(dto: MutableMapping[str, object], asset_transfer_fields: AssetTransferFields) -> None:
    dto["xaid"] = asset_transfer_fields.asset_id
    set_if(dto, "aamt", _encode_int(asset_transfer_fields.amount))
    dto["arcv"] = public_key_from_address(asset_transfer_fields.receiver)
    set_if(dto, "aclose", _encode_address(asset_transfer_fields.close_remainder_to))
    set_if(dto, "asnd", _encode_address(asset_transfer_fields.asset_sender))


def _add_asset_config_fields(dto: MutableMapping[str, object], asset_config_fields: AssetConfigFields) -> None:
    asset_params_dto: AssetParamsDto = {}
    asset_params_mut = cast(MutableMapping[str, object], asset_params_dto)
    set_if(asset_params_mut, "t", _encode_int(asset_config_fields.total))
    set_if(asset_params_mut, "dc", _encode_int(asset_config_fields.decimals))
    set_if(asset_params_mut, "df", _encode_bool(asset_config_fields.default_frozen))
    set_if(asset_params_mut, "un", asset_config_fields.unit_name or None)
    set_if(asset_params_mut, "an", asset_config_fields.asset_name or None)
    set_if(asset_params_mut, "au", asset_config_fields.url or None)
    set_if(asset_params_mut, "am", _encode_bytes(asset_config_fields.metadata_hash))
    set_if(asset_params_mut, "m", _encode_address(asset_config_fields.manager))
    set_if(asset_params_mut, "f", _encode_address(asset_config_fields.freeze))
    set_if(asset_params_mut, "c", _encode_address(asset_config_fields.clawback))
    set_if(asset_params_mut, "r", _encode_address(asset_config_fields.reserve))
    dto["caid"] = asset_config_fields.asset_id
    if asset_params_dto:
        dto["apar"] = asset_params_dto


def _add_asset_freeze_fields(dto: MutableMapping[str, object], asset_freeze_fields: AssetFreezeFields) -> None:
    dto["faid"] = asset_freeze_fields.asset_id
    dto["fadd"] = public_key_from_address(asset_freeze_fields.freeze_target)
    set_if(dto, "afrz", _encode_bool(asset_freeze_fields.frozen))


def _add_app_call_fields(dto: MutableMapping[str, object], app_call_fields: AppCallFields) -> None:
    dto["apid"] = app_call_fields.app_id
    dto["apan"] = app_call_fields.on_complete.value
    set_if(dto, "apap", _encode_bytes(app_call_fields.approval_program))
    set_if(dto, "apsu", _encode_bytes(app_call_fields.clear_state_program))
    if app_call_fields.global_state_schema:
        dto["apgs"] = {
            "nui": app_call_fields.global_state_schema.num_uints,
            "nbs": app_call_fields.global_state_schema.num_byte_slices,
        }
    if app_call_fields.local_state_schema:
        dto["apls"] = {
            "nui": app_call_fields.local_state_schema.num_uints,
            "nbs": app_call_fields.local_state_schema.num_byte_slices,
        }
    if app_call_fields.args:
        dto["apaa"] = list(app_call_fields.args)
    if app_call_fields.account_references:
        dto["apat"] = [public_key_from_address(a) for a in app_call_fields.account_references]
    if app_call_fields.app_references:
        dto["apfa"] = list(app_call_fields.app_references)
    if app_call_fields.asset_references:
        dto["apas"] = list(app_call_fields.asset_references)
    set_if(dto, "apep", _encode_int(app_call_fields.extra_program_pages))


def _add_key_registration_fields(
    dto: MutableMapping[str, object], key_registration_fields: KeyRegistrationFields
) -> None:
    set_if(dto, "votekey", _encode_bytes(key_registration_fields.vote_key))
    set_if(dto, "selkey", _encode_bytes(key_registration_fields.selection_key))
    set_if(dto, "votefst", _encode_int(key_registration_fields.vote_first))
    set_if(dto, "votelst", _encode_int(key_registration_fields.vote_last))
    set_if(dto, "votekd", _encode_int(key_registration_fields.vote_key_dilution))
    set_if(dto, "sprfkey", _encode_bytes(key_registration_fields.state_proof_key))
    set_if(dto, "nonpart", _encode_bool(key_registration_fields.non_participation))


def _add_heartbeat_fields(dto: MutableMapping[str, object], heartbeat_fields: HeartbeatFields) -> None:
    heartbeat_dto: HeartbeatDto = {}
    heartbeat_mut = cast(MutableMapping[str, object], heartbeat_dto)
    address_bytes = _encode_address(heartbeat_fields.address) if heartbeat_fields.address else None
    set_if(heartbeat_mut, "a", address_bytes)
    set_if(heartbeat_mut, "sd", _encode_bytes(heartbeat_fields.seed))
    set_if(heartbeat_mut, "vid", _encode_bytes(heartbeat_fields.vote_id))
    set_if(heartbeat_mut, "kd", _encode_int(heartbeat_fields.key_dilution, keep_zero=True))
    if heartbeat_fields.proof is not None:
        proof: HeartbeatProofDto = {}
        proof_mut = cast(MutableMapping[str, object], proof)
        set_if(proof_mut, "s", _encode_bytes(heartbeat_fields.proof.signature))
        set_if(proof_mut, "p", _encode_bytes(heartbeat_fields.proof.public_key))
        set_if(proof_mut, "p2", _encode_bytes(heartbeat_fields.proof.public_key_2))
        set_if(proof_mut, "p1s", _encode_bytes(heartbeat_fields.proof.public_key_1_signature))
        set_if(proof_mut, "p2s", _encode_bytes(heartbeat_fields.proof.public_key_2_signature))
        if proof:
            heartbeat_dto["prf"] = proof
    if heartbeat_dto:
        dto["hb"] = heartbeat_dto


def _add_state_proof_fields(dto: MutableMapping[str, object], state_proof_fields: StateProofFields) -> None:
    set_if(dto, "sptype", _encode_int(state_proof_fields.state_proof_type))
    if state_proof_fields.state_proof is not None:
        state_proof = state_proof_fields.state_proof
        payload: StateProofDto = {}
        payload_mut = cast(MutableMapping[str, object], payload)
        set_if(payload_mut, "c", _encode_bytes(state_proof.sig_commit))
        set_if(payload_mut, "w", _encode_int(state_proof.signed_weight, keep_zero=True))
        set_if(payload_mut, "S", _encode_state_proof_proof(state_proof.sig_proofs))
        set_if(payload_mut, "P", _encode_state_proof_proof(state_proof.part_proofs))
        set_if(payload_mut, "v", _encode_int(state_proof.merkle_signature_salt_version, keep_zero=True))
        positions = _encode_int_sequence(state_proof.positions_to_reveal)
        if positions:
            payload["pr"] = positions
        reveals = _encode_reveals(state_proof.reveals)
        if reveals is not None and reveals:
            payload["r"] = reveals
        if payload:
            dto["sp"] = payload
    if state_proof_fields.message is not None:
        message = state_proof_fields.message
        message_dto: StateProofMessageDto = {}
        message_mut = cast(MutableMapping[str, object], message_dto)
        set_if(message_mut, "b", _encode_bytes(message.block_headers_commitment))
        set_if(message_mut, "v", _encode_bytes(message.voters_commitment))
        set_if(message_mut, "P", _encode_int(message.ln_proven_weight, keep_zero=True))
        set_if(message_mut, "f", _encode_int(message.first_attested_round, keep_zero=True))
        set_if(message_mut, "l", _encode_int(message.last_attested_round, keep_zero=True))
        if message_dto:
            dto["spmsg"] = message_dto


def to_transaction_dto(tx: Transaction) -> TransactionDto:
    dto: TransactionDto = {
        "type": _to_type_str(tx.transaction_type),
        "snd": public_key_from_address(tx.sender),
        "fv": tx.first_valid,
        "lv": tx.last_valid,
    }
    dto_mut = cast(MutableMapping[str, object], dto)

    set_if(dto_mut, "gen", tx.genesis_id)
    set_if(dto_mut, "gh", _encode_bytes(tx.genesis_hash))
    set_if(dto_mut, "fee", _encode_int(tx.fee))
    set_if(dto_mut, "note", _encode_bytes(tx.note))
    set_if(dto_mut, "lx", _encode_bytes(tx.lease))
    set_if(dto_mut, "rekey", _encode_address(tx.rekey_to))
    set_if(dto_mut, "grp", _encode_bytes(tx.group))

    payment_fields = tx.payment
    if payment_fields is not None:
        _add_payment_fields(dto_mut, payment_fields)

    asset_transfer_fields = tx.asset_transfer
    if asset_transfer_fields is not None:
        _add_asset_transfer_fields(dto_mut, asset_transfer_fields)

    asset_config_fields = tx.asset_config
    if asset_config_fields is not None:
        _add_asset_config_fields(dto_mut, asset_config_fields)

    asset_freeze_fields = tx.asset_freeze
    if asset_freeze_fields is not None:
        _add_asset_freeze_fields(dto_mut, asset_freeze_fields)

    app_call_fields = tx.app_call
    if app_call_fields is not None:
        _add_app_call_fields(dto_mut, app_call_fields)

    key_registration_fields = tx.key_registration
    if key_registration_fields is not None:
        _add_key_registration_fields(dto_mut, key_registration_fields)

    heartbeat_fields = tx.heartbeat
    if heartbeat_fields is not None:
        _add_heartbeat_fields(dto_mut, heartbeat_fields)

    state_proof_fields = tx.state_proof
    if state_proof_fields is not None:
        _add_state_proof_fields(dto_mut, state_proof_fields)

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


def _is_default_like(value: object) -> bool:  # noqa: PLR0911
    if value is None:
        return True
    # primitives
    if isinstance(value, int) and value == 0:
        return True
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, bytes | bytearray) and len(value) == 0:
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
    canonical = _omit_defaults_and_sort(dict(dto))
    return encode_msgpack(canonical)


def encode_transaction(tx: Transaction) -> bytes:
    raw = encode_transaction_raw(tx)
    prefix = TRANSACTION_DOMAIN_SEPARATOR.encode()
    return prefix + raw


def encode_transactions(transactions: Iterable[Transaction]) -> list[bytes]:
    return [encode_transaction(tx) for tx in transactions]


def from_transaction_dto(dto: Mapping[str, object]) -> Transaction:  # noqa: C901, PLR0912, PLR0915
    type_value = dto.get("type")
    if not isinstance(type_value, str):
        raise ValueError("transaction dto missing type")
    ttype = _from_type_str(type_value)

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

    def get_bool(key: str) -> bool | None:
        v = dto.get(key)
        if isinstance(v, bool):
            return v
        return None

    sender = get_str_addr("snd") or ""
    first_valid = get_int("fv") or 0
    last_valid = get_int("lv") or 0
    fee = get_int("fee")
    genesis_id_value = dto.get("gen")
    genesis_id = genesis_id_value if isinstance(genesis_id_value, str) else None
    genesis_hash = get_bytes("gh")
    note = get_bytes("note")
    lease = get_bytes("lx")
    rekey_to = get_str_addr("rekey")
    group = get_bytes("grp")

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
        params = cast(Mapping[str, object], apar) if isinstance(apar, Mapping) else {}
        df_value = params.get("df") if params else None
        unit_name_raw = params.get("un") if params else None
        asset_name_raw = params.get("an") if params else None
        url_raw = params.get("au") if params else None
        metadata_raw = params.get("am") if params else None
        manager_raw = params.get("m") if params else None
        reserve_raw = params.get("r") if params else None
        freeze_raw = params.get("f") if params else None
        clawback_raw = params.get("c") if params else None

        metadata_bytes = _decode_bytes_like(metadata_raw) if metadata_raw is not None else None
        manager_bytes = _decode_bytes_like(manager_raw)
        reserve_bytes = _decode_bytes_like(reserve_raw)
        freeze_bytes = _decode_bytes_like(freeze_raw)
        clawback_bytes = _decode_bytes_like(clawback_raw)

        asset_config = AssetConfigFields(
            asset_id=get_int("caid") or 0,
            total=_decode_int_like(params.get("t")) if params else None,
            decimals=_decode_int_like(params.get("dc")) if params else None,
            default_frozen=df_value if isinstance(df_value, bool) else None,
            unit_name=unit_name_raw if isinstance(unit_name_raw, str) else None,
            asset_name=asset_name_raw if isinstance(asset_name_raw, str) else None,
            url=url_raw if isinstance(url_raw, str) else None,
            metadata_hash=metadata_bytes,
            manager=address_from_public_key(manager_bytes) if manager_bytes is not None else None,
            reserve=address_from_public_key(reserve_bytes) if reserve_bytes is not None else None,
            freeze=address_from_public_key(freeze_bytes) if freeze_bytes is not None else None,
            clawback=address_from_public_key(clawback_bytes) if clawback_bytes is not None else None,
        )

    asset_freeze: AssetFreezeFields | None = None
    if any(k in dto for k in ("faid", "fadd", "afrz")):
        asset_freeze = AssetFreezeFields(
            asset_id=get_int("faid") or 0,
            freeze_target=get_str_addr("fadd") or "",
            frozen=bool(dto.get("afrz")) if isinstance(dto.get("afrz"), bool) else False,
        )

    app_call: AppCallFields | None = None
    if any(
        k in dto
        for k in (
            "apid",
            "apan",
            "apap",
            "apsu",
            "apgs",
            "apls",
            "apaa",
            "apat",
            "apfa",
            "apas",
            "apep",
        )
    ):
        apgs = dto.get("apgs")
        apls = dto.get("apls")
        args_payload = dto.get("apaa")
        apat_payload = dto.get("apat")
        apfa_payload = dto.get("apfa")
        apas_payload = dto.get("apas")

        args_tuple: tuple[bytes, ...] | None = None
        if isinstance(args_payload, list):
            coerced_args = [bytes(arg) for arg in args_payload if isinstance(arg, bytes | bytearray)]
            if coerced_args:
                args_tuple = tuple(coerced_args)

        account_refs_tuple: tuple[str, ...] | None = None
        if isinstance(apat_payload, list):
            accounts = [address_from_public_key(bytes(a)) for a in apat_payload if isinstance(a, bytes | bytearray)]
            if accounts:
                account_refs_tuple = tuple(accounts)

        app_refs_tuple: tuple[int, ...] | None = None
        if isinstance(apfa_payload, list):
            app_refs = [int(x) for x in apfa_payload if isinstance(x, int)]
            if app_refs:
                app_refs_tuple = tuple(app_refs)

        asset_refs_tuple: tuple[int, ...] | None = None
        if isinstance(apas_payload, list):
            asset_refs = [int(x) for x in apas_payload if isinstance(x, int)]
            if asset_refs:
                asset_refs_tuple = tuple(asset_refs)
        apan_value = dto.get("apan")
        on_complete_value = apan_value if isinstance(apan_value, int) else 0
        app_call = AppCallFields(
            app_id=get_int("apid") or 0,
            on_complete=OnApplicationComplete(on_complete_value),
            approval_program=get_bytes("apap"),
            clear_state_program=get_bytes("apsu"),
            global_state_schema=(
                None
                if not isinstance(apgs, Mapping)
                else StateSchema(
                    num_uints=_decode_int_like(apgs.get("nui")) or 0,
                    num_byte_slices=_decode_int_like(apgs.get("nbs")) or 0,
                )
            ),
            local_state_schema=(
                None
                if not isinstance(apls, Mapping)
                else StateSchema(
                    num_uints=_decode_int_like(apls.get("nui")) or 0,
                    num_byte_slices=_decode_int_like(apls.get("nbs")) or 0,
                )
            ),
            args=args_tuple,
            account_references=account_refs_tuple,
            app_references=app_refs_tuple,
            asset_references=asset_refs_tuple,
            extra_program_pages=get_int("apep"),
        )

    key_registration: KeyRegistrationFields | None = None
    if any(k in dto for k in ("votekey", "selkey", "votefst", "votelst", "votekd", "sprfkey", "nonpart")):
        key_registration = KeyRegistrationFields(
            vote_key=get_bytes("votekey"),
            selection_key=get_bytes("selkey"),
            vote_first=get_int("votefst"),
            vote_last=get_int("votelst"),
            vote_key_dilution=get_int("votekd"),
            state_proof_key=get_bytes("sprfkey"),
            non_participation=get_bool("nonpart"),
        )

    heartbeat = _decode_heartbeat(dto.get("hb"))

    state_proof_fields: StateProofFields | None = None
    if any(key in dto for key in ("sptype", "sp", "spmsg")):
        state_proof_fields = StateProofFields(
            state_proof_type=get_int("sptype"),
            state_proof=_decode_state_proof(dto.get("sp")),
            message=_decode_state_proof_message(dto.get("spmsg")),
        )

    if ttype is TransactionType.KeyRegistration and key_registration is None:
        key_registration = KeyRegistrationFields()

    return Transaction(
        transaction_type=ttype,
        sender=sender,
        first_valid=first_valid,
        last_valid=last_valid,
        fee=fee,
        genesis_id=genesis_id,
        genesis_hash=genesis_hash,
        note=note,
        lease=lease,
        rekey_to=rekey_to,
        group=group,
        payment=payment,
        asset_transfer=asset_transfer,
        asset_config=asset_config,
        app_call=app_call,
        key_registration=key_registration,
        asset_freeze=asset_freeze,
        heartbeat=heartbeat,
        state_proof=state_proof_fields,
    )


def decode_transaction(encoded: bytes) -> Transaction:
    if not encoded:
        raise ValueError("attempted to decode 0 bytes")
    prefix = TRANSACTION_DOMAIN_SEPARATOR.encode()
    if encoded[: len(prefix)] == prefix:
        payload = encoded[len(prefix) :]
    else:
        payload = encoded
    raw: object = decode_msgpack(payload)
    if not isinstance(raw, dict):
        raise ValueError("decoded msgpack is not a dict")
    dto = cast(dict[str, object], raw)
    return from_transaction_dto(dto)


def decode_transactions(encoded_transactions: Iterable[bytes]) -> list[Transaction]:
    return [decode_transaction(item) for item in encoded_transactions]


def get_encoded_transaction_type(encoded_transaction: bytes) -> TransactionType:
    return decode_transaction(encoded_transaction).transaction_type
