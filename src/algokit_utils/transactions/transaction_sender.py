import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from algosdk.transaction import wait_for_confirmation
from algosdk.v2client.algod import AlgodClient

from algokit_utils.applications.app_manager import AppManager
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.transactions.transaction_composer import (
    PaymentParams,
    TransactionComposer,
)

logger = logging.getLogger(__name__)
TxnParam = TypeVar("TxnParam")
TxnResult = TypeVar("TxnResult")


@dataclass
class SendTransactionResult(Generic[TxnResult]):
    """Result of sending a transaction"""

    confirmation: dict[str, Any]
    tx_id: str
    return_value: TxnResult | None = None


class AlgorandClientTransactionSender:
    """Orchestrates sending transactions for AlgorandClient."""

    def __init__(
        self,
        new_group: Callable[[], TransactionComposer],
        asset_manager: AssetManager,
        app_manager: AppManager,
        algod_client: AlgodClient,
    ) -> None:
        self._new_group = new_group
        self._asset_manager = asset_manager
        self._app_manager = app_manager
        self._algod_client = algod_client

    def new_group(self) -> TransactionComposer:
        """Create a new transaction group"""
        return self._new_group()

    def _send(
        self,
        c: Callable[[TransactionComposer], Callable[[TxnParam], TransactionComposer]],
        log: dict[str, Callable[[TxnParam, Any], str]] | None = None,
    ) -> Callable[[TxnParam], SendTransactionResult[Any]]:
        """Generic method to send transactions with logging."""

        def send_transaction(params: TxnParam) -> SendTransactionResult[Any]:
            composer = self._new_group()
            c(composer)(params)

            if log and log.get("pre_log"):
                transaction = composer.build().transactions[-1].txn
                logger.debug(log["pre_log"](params, transaction))

            result = composer.send()

            if log and log.get("post_log"):
                logger.debug(log["post_log"](params, result))

            confirmation = wait_for_confirmation(self._algod_client, result.tx_ids[0])
            return SendTransactionResult(
                confirmation=confirmation,
                tx_id=result.tx_ids[0],
            )

        return send_transaction

    @property
    def payment(self) -> Callable[[PaymentParams], SendTransactionResult[None]]:
        """Send a payment transaction"""
        return self._send(
            lambda c: c.add_payment,
            {
                "pre_log": lambda params, txn: (
                    f"Sending {params.amount.micro_algos} µALGO from {params.sender} "
                    f"to {params.receiver} via transaction {txn.get_txid()}"
                )
            },
        )
