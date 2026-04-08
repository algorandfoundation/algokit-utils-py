import pytest

from algokit_transact.signer import AddressWithSigners
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def sender(algorand: AlgorandClient) -> AddressWithSigners:
    account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        account, dispenser, AlgoAmount.from_algo(10), min_funding_increment=AlgoAmount.from_algo(1)
    )
    return account


@pytest.fixture
def receiver(algorand: AlgorandClient) -> AddressWithSigners:
    account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        account, dispenser, AlgoAmount.from_algo(1), min_funding_increment=AlgoAmount.from_algo(1)
    )
    return account


@pytest.mark.localnet
def test_pending_transaction_broadcast(
    algorand: AlgorandClient, sender: AddressWithSigners, receiver: AddressWithSigners
) -> None:
    """Test broadcasting a transaction and retrieving pending transaction information."""
    # Get the algod_client from the AlgorandClient so we use the same client consistently
    algod_client = algorand.client.algod

    # Build payment transaction using Algokit
    txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=sender.addr,
            receiver=receiver.addr,
            amount=AlgoAmount.from_micro_algo(500_000),
            note=b"Test payment transaction",
        )
    )

    # Sign the transaction
    signed_blob = sender.signer([txn], [0])[0]

    # Send the signed transaction using the raw algod_client
    response = algod_client.send_raw_transaction(signed_blob)
    # Get pending transaction information
    pending_txn = algod_client.pending_transaction_information(txid=response.tx_id)

    # Verify pending transaction response (typed model)
    assert pending_txn.pool_error == ""
    assert pending_txn.confirmed_round is not None
    assert pending_txn.confirmed_round > 0
