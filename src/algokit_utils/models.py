import dataclasses
from typing import Any

from algosdk.abi import Method


@dataclasses.dataclass
class Account:
    """Holds the private_key and address for an account"""

    private_key: str
    address: str


@dataclasses.dataclass(kw_only=True)
class TransactionResponse:
    """Response for a non ABI call"""

    tx_id: str
    """Transaction Id"""
    confirmed_round: int | None
    """Round transaction was confirmed, `None` if call was a from a dry-run"""


@dataclasses.dataclass(kw_only=True)
class ABITransactionResponse(TransactionResponse):
    """Response for an ABI call"""

    raw_value: bytes
    """The raw response before ABI decoding"""
    return_value: Any
    """Decoded ABI result"""
    decode_error: Exception | None
    """Details of error that occurred when attempting to decode raw_value"""
    tx_info: dict
    """Details of transaction"""
    method: Method
    """ABI method used to make call"""
