"""Shared helpers for Algokit Transact pytest suites.

This module loads test data from the data factory, mirroring the approach in
the TypeScript workspace's common.ts.
"""

import base64
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from algokit_common import public_key_from_address
from algokit_transact import (
    Transaction,
    from_transaction_dto,
)

TESTS_DIR = Path(__file__).resolve().parent
DATA_FACTORY_PATH = TESTS_DIR / "polytest_resources" / "data-factory" / "data"


@dataclass(frozen=True)
class SingleSigner:
    """Single signer with secret key and public key (mirrors TS { SK, SignatureVerifier })."""

    sk: bytes  # 64-byte ed25519 private key
    pk: bytes  # 32-byte public key (signature verifier)


@dataclass(frozen=True)
class SignerInfo:
    """Signer information from data factory (mirrors TS SignerInfo)."""

    single_signer: SingleSigner | None
    msig_signers: tuple[SingleSigner, ...] | None
    lsig: bytes | None


@dataclass(frozen=True)
class TransactionTestData:
    """Test data loaded from data factory files (mirrors TS TransactionTestData)."""

    id: str
    transaction: Transaction
    unsigned_bytes: bytes
    signed_bytes: bytes
    signer: SignerInfo


def _b64_decode(value: str | None) -> bytes | None:
    """Decode base64 string to bytes."""
    if value is None:
        return None
    return base64.b64decode(value)


def _parse_signer(signer: dict[str, Any]) -> SignerInfo:
    """Parse signer information from data factory format."""
    single_raw = signer.get("singleSigner")
    msig_raw = signer.get("msigSigners")

    single_signer = None
    if single_raw:
        sk = _b64_decode(single_raw.get("SK"))
        pk = _b64_decode(single_raw.get("SignatureVerifier"))
        if sk and pk:
            single_signer = SingleSigner(sk=sk, pk=pk)

    msig_signers = None
    if msig_raw and isinstance(msig_raw, list):
        signers = [
            SingleSigner(sk=sk, pk=pk)
            for s in msig_raw
            if (sk := _b64_decode(s.get("SK"))) and (pk := _b64_decode(s.get("SignatureVerifier")))
        ]
        msig_signers = tuple(signers) if signers else None

    lsig = _b64_decode(signer.get("lsig")) if isinstance(signer.get("lsig"), str) else None

    return SignerInfo(single_signer=single_signer, msig_signers=msig_signers, lsig=lsig)


_ADDR = "addr"  # 58-char address string -> 32-byte public key
_BINARY = "binary"  # base64 string -> bytes
_BINARY_LIST = "binary[]"  # list of base64 strings -> list of bytes
_ADDR_LIST = "addr[]"  # list of address strings -> list of public keys


def _dict_of(schema: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Marker for a dict where each value follows the given schema."""
    return ("dict_of", schema)


_MERKLE_PROOF: dict[str, Any] = {"pth": _BINARY_LIST, "hsh": {}}
_FALCON_VERIFIER: dict[str, Any] = {"k": _BINARY}
_MSIG_VERIFIER: dict[str, Any] = {"cmt": _BINARY}
_FALCON_SIG: dict[str, Any] = {"sig": _BINARY, "prf": _MERKLE_PROOF, "vkey": _FALCON_VERIFIER}
_SIGSLOT: dict[str, Any] = {"s": _FALCON_SIG}
_PARTICIPANT: dict[str, Any] = {"p": _MSIG_VERIFIER}
_REVEAL: dict[str, Any] = {"p": _PARTICIPANT, "s": _SIGSLOT}

# Transaction schema
_TX_SCHEMA: dict[str, Any] = {
    "snd": _ADDR,
    "rcv": _ADDR,
    "close": _ADDR,
    "asnd": _ADDR,
    "aclose": _ADDR,
    "fadd": _ADDR,
    "rekey": _ADDR,
    "arcv": _ADDR,
    "gh": _BINARY,
    "note": _BINARY,
    "lx": _BINARY,
    "grp": _BINARY,
    "sig": _BINARY,
    "apap": _BINARY,
    "apsu": _BINARY,
    "votekey": _BINARY,
    "selkey": _BINARY,
    "sprfkey": _BINARY,
    "am": _BINARY,
    "apaa": _BINARY_LIST,
    "apat": _ADDR_LIST,
    "apar": {"c": _ADDR, "f": _ADDR, "m": _ADDR, "r": _ADDR, "am": _BINARY},
    "hb": {
        "a": _ADDR,
        "sd": _BINARY,
        "vid": _BINARY,
        "prf": {"p": _BINARY, "p1s": _BINARY, "p2": _BINARY, "p2s": _BINARY, "s": _BINARY},
    },
    "spmsg": {"b": _BINARY, "v": _BINARY},
    "sp": {"c": _BINARY, "P": _MERKLE_PROOF, "S": _MERKLE_PROOF, "r": _dict_of(_REVEAL)},
}


def _apply_schema(data: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Apply schema transformations to nested data."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        field_schema = schema.get(key)
        if field_schema == _ADDR and isinstance(value, str) and len(value) == 58:
            result[key] = public_key_from_address(value)
        elif field_schema == _BINARY and isinstance(value, str):
            result[key] = base64.b64decode(value)
        elif field_schema == _BINARY_LIST and isinstance(value, list):
            result[key] = [base64.b64decode(v) if isinstance(v, str) else v for v in value]
        elif field_schema == _ADDR_LIST and isinstance(value, list):
            result[key] = [public_key_from_address(v) if isinstance(v, str) and len(v) == 58 else v for v in value]
        elif isinstance(field_schema, dict) and isinstance(value, dict):
            result[key] = _apply_schema(value, field_schema)
        elif isinstance(field_schema, tuple) and field_schema[0] == "dict_of" and isinstance(value, dict):
            item_schema = field_schema[1]
            result[key] = {k: _apply_schema(v, item_schema) for k, v in value.items() if isinstance(v, dict)}
        else:
            result[key] = value
    return result


def from_transaction_json(data: dict[str, Any]) -> Transaction:
    """Decode a transaction from JSON format (address strings, base64 binary)."""
    wire_format = _apply_schema(data, _TX_SCHEMA)
    return from_transaction_dto(wire_format)


@lru_cache(maxsize=32)
def load_test_data(name: str) -> TransactionTestData:
    """Load test data from the data factory.

    Available names: simplePayment, optInAssetTransfer, simpleAssetTransfer,
    assetCreate, assetDestroy, assetConfig, appCall, appCreate, appUpdate, appDelete,
    onlineKeyRegistration, offlineKeyRegistration, nonParticipationKeyRegistration,
    assetFreeze, assetUnfreeze, heartbeat, stateProof, lsigPayment, msigPayment,
    msigDelegatedPayment, singleDelegatedPayment
    """
    file_path = DATA_FACTORY_PATH / f"{name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Data factory file not found: {file_path}")

    data = json.loads(file_path.read_text())
    txn_json = data["stxn"]["txn"]
    transaction = from_transaction_json(txn_json)

    return TransactionTestData(
        id=data["id"],
        transaction=transaction,
        unsigned_bytes=_b64_decode(data["txnBlob"]) or b"",
        signed_bytes=_b64_decode(data["stxnBlob"]) or b"",
        signer=_parse_signer(data.get("signer", {})),
    )


__all__ = ["SignerInfo", "SingleSigner", "TransactionTestData", "load_test_data"]
