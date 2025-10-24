from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TransactionType(Enum):
    Payment = "pay"
    AssetTransfer = "axfer"
    AssetFreeze = "afrz"
    AssetConfig = "acfg"
    KeyRegistration = "keyreg"
    AppCall = "appl"
    StateProof = "stpf"
    Heartbeat = "hb"


class OnApplicationComplete(Enum):
    NoOp = 0
    OptIn = 1
    CloseOut = 2
    ClearState = 3
    UpdateApplication = 4
    DeleteApplication = 5


@dataclass(slots=True, frozen=True)
class StateSchema:
    num_uints: int
    num_byte_slices: int


@dataclass(slots=True, frozen=True)
class PaymentFields:
    amount: int
    receiver: str
    close_remainder_to: str | None = None


@dataclass(slots=True, frozen=True)
class AssetTransferFields:
    asset_id: int
    amount: int
    receiver: str
    close_remainder_to: str | None = None
    asset_sender: str | None = None


@dataclass(slots=True, frozen=True)
class AssetConfigFields:
    asset_id: int
    total: int | None = None
    decimals: int | None = None
    default_frozen: bool | None = None
    unit_name: str | None = None
    asset_name: str | None = None
    url: str | None = None
    metadata_hash: bytes | None = None
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass(slots=True, frozen=True)
class AppCallFields:
    app_id: int
    on_complete: OnApplicationComplete = OnApplicationComplete.NoOp
    approval_program: bytes | None = None
    clear_state_program: bytes | None = None
    global_state_schema: StateSchema | None = None
    local_state_schema: StateSchema | None = None
    args: tuple[bytes, ...] | None = None
    account_references: tuple[str, ...] | None = None
    app_references: tuple[int, ...] | None = None
    asset_references: tuple[int, ...] | None = None
    extra_program_pages: int | None = None


@dataclass(slots=True, frozen=True)
class KeyRegistrationFields:
    vote_key: bytes | None = None
    selection_key: bytes | None = None
    vote_first: int | None = None
    vote_last: int | None = None
    vote_key_dilution: int | None = None
    state_proof_key: bytes | None = None
    non_participation: bool | None = None


@dataclass(slots=True, frozen=True)
class AssetFreezeFields:
    asset_id: int
    freeze_target: str
    frozen: bool


@dataclass(slots=True, frozen=True)
class HeartbeatProof:
    signature: bytes | None = None
    public_key: bytes | None = None
    public_key_2: bytes | None = None
    public_key_1_signature: bytes | None = None
    public_key_2_signature: bytes | None = None


@dataclass(slots=True, frozen=True)
class HeartbeatFields:
    address: str | None = None
    proof: HeartbeatProof | None = None
    seed: bytes | None = None
    vote_id: bytes | None = None
    key_dilution: int | None = None


@dataclass(slots=True, frozen=True)
class HashFactory:
    hash_type: int | None = None


@dataclass(slots=True, frozen=True)
class MerkleArrayProof:
    path: tuple[bytes, ...] | None = None
    hash_factory: HashFactory | None = None
    tree_depth: int | None = None


@dataclass(slots=True, frozen=True)
class MerkleSignatureVerifier:
    commitment: bytes | None = None
    key_lifetime: int | None = None


@dataclass(slots=True, frozen=True)
class Participant:
    verifier: MerkleSignatureVerifier | None = None
    weight: int | None = None


@dataclass(slots=True, frozen=True)
class FalconVerifier:
    public_key: bytes | None = None


@dataclass(slots=True, frozen=True)
class FalconSignatureStruct:
    signature: bytes | None = None
    vector_commitment_index: int | None = None
    proof: MerkleArrayProof | None = None
    verifying_key: FalconVerifier | None = None


@dataclass(slots=True, frozen=True)
class SigslotCommit:
    sig: FalconSignatureStruct | None = None
    lower_sig_weight: int | None = None


@dataclass(slots=True, frozen=True)
class Reveal:
    participant: Participant | None = None
    sigslot: SigslotCommit | None = None
    position: int | None = None


@dataclass(slots=True, frozen=True)
class StateProof:
    sig_commit: bytes | None = None
    signed_weight: int | None = None
    sig_proofs: MerkleArrayProof | None = None
    part_proofs: MerkleArrayProof | None = None
    merkle_signature_salt_version: int | None = None
    reveals: tuple[Reveal, ...] | None = None
    positions_to_reveal: tuple[int, ...] | None = None


@dataclass(slots=True, frozen=True)
class StateProofMessage:
    block_headers_commitment: bytes | None = None
    voters_commitment: bytes | None = None
    ln_proven_weight: int | None = None
    first_attested_round: int | None = None
    last_attested_round: int | None = None


@dataclass(slots=True, frozen=True)
class StateProofFields:
    state_proof_type: int | None = None
    state_proof: StateProof | None = None
    message: StateProofMessage | None = None


@dataclass(slots=True, frozen=True)
class MultisigSubsignature:
    address: str
    signature: bytes | None = None


@dataclass(slots=True, frozen=True)
class MultisigSignature:
    version: int
    threshold: int
    subsignatures: tuple[MultisigSubsignature, ...]


@dataclass(slots=True, frozen=True)
class LogicSignature:
    logic: bytes
    args: tuple[bytes, ...] | None = None
    signature: bytes | None = None
    multi_signature: MultisigSignature | None = None


@dataclass(slots=True, frozen=True)
class Transaction:
    transaction_type: TransactionType
    sender: str
    first_valid: int
    last_valid: int
    fee: int | None = None
    genesis_hash: bytes | None = None
    genesis_id: str | None = None
    note: bytes | None = None
    rekey_to: str | None = None
    lease: bytes | None = None
    group: bytes | None = None

    # one-of type-specific fields
    payment: PaymentFields | None = None
    asset_transfer: AssetTransferFields | None = None
    asset_config: AssetConfigFields | None = None
    app_call: AppCallFields | None = None
    key_registration: KeyRegistrationFields | None = None
    asset_freeze: AssetFreezeFields | None = None
    heartbeat: HeartbeatFields | None = None
    state_proof: StateProofFields | None = None


@dataclass(slots=True, frozen=True)
class SignedTransaction:
    transaction: Transaction
    signature: bytes | None = None
    multi_signature: MultisigSignature | None = None
    logic_signature: LogicSignature | None = None
    auth_address: str | None = None
