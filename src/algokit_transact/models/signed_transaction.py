from dataclasses import dataclass, field

from algokit_transact.codec.serde import addr, nested, wire
from algokit_transact.models.transaction import Transaction
from algokit_transact.signing.logic_signature import LogicSignature
from algokit_transact.signing.types import MultisigSignature


@dataclass(slots=True, frozen=True)
class SignedTransaction:
    transaction: Transaction = field(metadata=nested("txn", Transaction))
    signature: bytes | None = field(default=None, metadata=wire("sig"))
    multi_signature: MultisigSignature | None = field(
        default=None,
        metadata=nested("msig", MultisigSignature),
    )
    logic_signature: LogicSignature | None = field(
        default=None,
        metadata=nested("lsig", LogicSignature),
    )
    auth_address: str | None = field(default=None, metadata=addr("sgnr"))
