from dataclasses import dataclass, field

from algokit_transact.codec.serde import addr, nested, wire
from algokit_transact.models.transaction import Transaction
from algokit_transact.signing.logic_signature import LogicSigSignature
from algokit_transact.signing.types import MultisigSignature


@dataclass(slots=True, frozen=True)
class SignedTransaction:
    txn: Transaction = field(metadata=nested("txn", Transaction))
    sig: bytes | None = field(default=None, metadata=wire("sig"))
    msig: MultisigSignature | None = field(
        default=None,
        metadata=nested("msig", MultisigSignature),
    )
    lsig: LogicSigSignature | None = field(
        default=None,
        metadata=nested("lsig", LogicSigSignature),
    )
    auth_address: str | None = field(default=None, metadata=addr("sgnr"))
