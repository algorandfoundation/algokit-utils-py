from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .dryrun_txn_result import DryrunTxnResult


@dataclass(slots=True)
class TealDryrunResponseModel:
    error: str = field(
        metadata=wire("error"),
    )
    protocol_version: str = field(
        metadata=wire("protocol-version"),
    )
    txns: list[DryrunTxnResult] = field(
        metadata=wire(
            "txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: DryrunTxnResult, raw),
        ),
    )
