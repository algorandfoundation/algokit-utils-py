import dataclasses
from typing import Any

from algosdk.abi import Method


@dataclasses.dataclass
class Account:
    private_key: str
    address: str


@dataclasses.dataclass(kw_only=True)
class TransactionResponse:
    tx_id: str
    confirmed_round: int | None


@dataclasses.dataclass(kw_only=True)
class ABITransactionResponse(TransactionResponse):
    raw_value: bytes
    return_value: Any
    decode_error: Exception | None
    tx_info: dict
    method: Method
