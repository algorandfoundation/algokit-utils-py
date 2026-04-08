# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_sequence, encode_bytes_sequence


@dataclass(slots=True)
class ImportMultisigRequest:
    """
    The request for `POST /v1/multisig/import`
    """

    multisig_version: int = field(
        default=0,
        metadata=wire("multisig_version"),
    )
    public_keys: list[bytes] = field(
        default_factory=list,
        metadata=wire(
            "pks",
            encode=encode_bytes_sequence,
            decode=decode_bytes_sequence,
        ),
    )
    threshold: int = field(
        default=0,
        metadata=wire("threshold"),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
