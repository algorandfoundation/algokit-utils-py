import pytest

from algokit_indexer_client import ClientConfig, IndexerClient
from algokit_utils.algorand import AlgorandClient
from algokit_transact.signer import AddressWithSigners
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams
from tests.modules.indexer_client.common import fund_account, wait_for_indexer


@pytest.fixture
def funded_account(algorand_localnet: AlgorandClient) -> AddressWithSigners:
    account = algorand_localnet.account.random()
    fund_account(algorand_localnet, account)
    algorand_localnet.set_signer(sender=account.addr, signer=account.signer)
    return account


@pytest.fixture
def localnet_indexer_client() -> IndexerClient:
    """Create an indexer client connected to localnet."""
    config = ClientConfig(
        base_url="http://localhost:8980",
        token="a" * 64,
    )
    return IndexerClient(config)


@pytest.mark.localnet
def test_search_transactions_finds_recent_payment(
    algorand_localnet: AlgorandClient,
    funded_account: AddressWithSigners,
    localnet_indexer_client: IndexerClient,
) -> None:
    """Test searching for transactions using localnet indexer.

    NOTE: This test requires localnet to be running with indexer.
    """
    receiver = algorand_localnet.account.random()
    algorand_localnet.account.ensure_funded(
        receiver,
        funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    send_result = algorand_localnet.send.payment(
        PaymentParams(
            sender=funded_account.addr,
            receiver=receiver.addr,
            amount=AlgoAmount.from_algo(1),
            note=b"indexer test payment",
        )
    )

    tx_id = send_result.tx_id
    assert tx_id

    wait_for_indexer(localnet_indexer_client, tx_id)

    lookup = localnet_indexer_client.lookup_transaction_by_id(tx_id)
    assert lookup.transaction
    transaction = lookup.transaction
    assert transaction.tx_type == "pay"
    assert transaction.sender == funded_account.addr
    assert transaction.payment_transaction
    assert transaction.payment_transaction.receiver == receiver.addr
    assert transaction.payment_transaction.amount == 1_000_000

    search = localnet_indexer_client.search_for_transactions(txid=tx_id)
    assert search.transactions
    assert search.transactions[0].id_ == tx_id
