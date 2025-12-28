# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_fixed_bytes, encode_fixed_bytes


@dataclass(slots=True)
class TransactionParametersResponse:
    """
    TransactionParams contains the parameters that help a client construct
    a new transaction.
    """

    consensus_version: str = field(
        default="",
        metadata=wire("consensus-version"),
    )
    fee: int = field(
        default=0,
        metadata=wire("fee"),
    )
    genesis_hash: bytes = field(
        default=b"",
        metadata=wire(
            "genesis-hash",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    genesis_id: str = field(
        default="",
        metadata=wire("genesis-id"),
    )
    last_round: int = field(
        default=0,
        metadata=wire("last-round"),
    )
    min_fee: int = field(
        default=0,
        metadata=wire("min-fee"),
    )
