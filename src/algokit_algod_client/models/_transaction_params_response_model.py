# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TransactionParamsResponseModel:
    """
    TransactionParams contains the parameters that help a client construct
    a new transaction.
    """

    consensus_version: str = field(
        metadata=wire("consensus-version"),
    )
    fee: int = field(
        metadata=wire("fee"),
    )
    genesis_hash: bytes = field(
        metadata=wire("genesis-hash"),
    )
    genesis_id: str = field(
        metadata=wire("genesis-id"),
    )
    last_round: int = field(
        metadata=wire("last-round"),
    )
    min_fee: int = field(
        metadata=wire("min-fee"),
    )
