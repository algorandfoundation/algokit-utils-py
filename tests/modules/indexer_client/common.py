import time
from http import HTTPStatus

from algokit_indexer_client import IndexerClient
from algokit_indexer_client.exceptions import UnexpectedStatusError
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.account import SigningAccount
from algokit_utils.models.amount import AlgoAmount


def fund_account(algorand: AlgorandClient, account: SigningAccount) -> None:
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        account,
        dispenser,
        min_spending_balance=AlgoAmount.from_algo(10),
        min_funding_increment=AlgoAmount.from_algo(10),
    )


def wait_for_indexer(indexer: IndexerClient, txid: str, *, timeout: float = 20.0, interval: float = 0.2) -> None:
    deadline = time.time() + timeout
    while True:
        try:
            indexer.lookup_transaction(txid)
            return
        except UnexpectedStatusError as exc:  # pragma: no cover - exercise via tests
            if exc.status_code is HTTPStatus.NOT_FOUND and time.time() < deadline:
                time.sleep(interval)
                continue
            raise
