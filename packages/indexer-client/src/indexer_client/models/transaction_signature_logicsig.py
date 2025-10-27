from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .transaction_signature_multisig import TransactionSignatureMultisig


@dataclass(slots=True)
class TransactionSignatureLogicsig:
    r"""
    \[lsig\] Programatic transaction signature.

    Definition:
    data/transactions/logicsig.go
    """

    logic: bytes = field(
        metadata=wire("logic"),
    )
    args: list[str] | None = field(
        default=None,
        metadata=wire("args"),
    )
    logic_multisig_signature: TransactionSignatureMultisig | None = field(
        default=None,
        metadata=nested("logic-multisig-signature", lambda: TransactionSignatureMultisig),
    )
    multisig_signature: TransactionSignatureMultisig | None = field(
        default=None,
        metadata=nested("multisig-signature", lambda: TransactionSignatureMultisig),
    )
    signature: bytes | None = field(
        default=None,
        metadata=wire("signature"),
    )
