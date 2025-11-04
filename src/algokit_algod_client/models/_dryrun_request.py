# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire
from algokit_transact.models.signed_transaction import SignedTransaction

from ._account import Account
from ._application import Application
from ._dryrun_source import DryrunSource
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class DryrunRequest:
    """
    Request data type for dryrun endpoint. Given the Transactions and simulated ledger state
    upload, run TEAL scripts and return debugging information.
    """

    accounts: list[Account] = field(
        metadata=wire(
            "accounts",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Account, raw),
        ),
    )
    apps: list[Application] = field(
        metadata=wire(
            "apps",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Application, raw),
        ),
    )
    latest_timestamp: int = field(
        metadata=wire("latest-timestamp"),
    )
    protocol_version: str = field(
        metadata=wire("protocol-version"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    sources: list[DryrunSource] = field(
        metadata=wire(
            "sources",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: DryrunSource, raw),
        ),
    )
    txns: list[SignedTransaction] = field(
        metadata=wire(
            "txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTransaction, raw),
        ),
    )
