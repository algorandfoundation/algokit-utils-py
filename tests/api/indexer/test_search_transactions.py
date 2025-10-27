from __future__ import annotations

import pytest
from indexer_client.client import IndexerClient

from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.account import SigningAccount
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams
from tests.api.indexer.common import fund_account, wait_for_indexer


@pytest.fixture
def funded_account(algorand_localnet: AlgorandClient) -> SigningAccount:
    account = algorand_localnet.account.random()
    fund_account(algorand_localnet, account)
    algorand_localnet.set_signer(sender=account.address, signer=account.signer)
    return account


def test_search_transactions_finds_recent_payment(
    algorand_localnet: AlgorandClient,
    funded_account: SigningAccount,
    indexer_client: IndexerClient,
) -> None:
    receiver = algorand_localnet.account.random()
    algorand_localnet.account.ensure_funded(
        receiver,
        funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    send_result = algorand_localnet.send.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=receiver.address,
            amount=AlgoAmount.from_algo(1),
            note=b"indexer test payment",
        )
    )

    tx_id = send_result.tx_id
    assert tx_id

    wait_for_indexer(indexer_client, tx_id)

    lookup = indexer_client.lookup_transaction(tx_id)
    assert lookup.transaction
    transaction = lookup.transaction
    assert transaction.tx_type == "pay"
    assert transaction.sender == funded_account.address
    assert transaction.payment_transaction
    assert transaction.payment_transaction.receiver == receiver.address
    assert transaction.payment_transaction.amount == 1_000_000

    search = indexer_client.search_for_transactions(txid=tx_id)
    assert search.transactions
    assert search.transactions[0].id_ == tx_id
