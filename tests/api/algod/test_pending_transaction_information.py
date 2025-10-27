import base64

import pytest
from algod_client import AlgodClient
from algosdk import encoding, transaction

from algokit_utils import SigningAccount
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.amount import AlgoAmount


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def sender(algorand: AlgorandClient) -> SigningAccount:
    account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        account, dispenser, AlgoAmount.from_algo(10), min_funding_increment=AlgoAmount.from_algo(1)
    )
    return account


@pytest.fixture
def receiver(algorand: AlgorandClient) -> SigningAccount:
    account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        account, dispenser, AlgoAmount.from_algo(1), min_funding_increment=AlgoAmount.from_algo(1)
    )
    return account


def test_pending_transaction_broadcast(
    algod_client: AlgodClient, algorand: AlgorandClient, sender: SigningAccount, receiver: SigningAccount
) -> None:
    """Test broadcasting a transaction and retrieving pending transaction information."""
    # Get transaction parameters from AlgorandClient's algod
    params = algorand.client.algod.suggested_params()

    # Build payment transaction using algosdk
    txn = transaction.PaymentTxn(
        sender=sender.address,
        sp=params,
        receiver=receiver.address,
        amt=500_000,  # 0.5 ALGO
        note=b"Test payment transaction",
    )

    # Sign the transaction
    signed_txn = encoding.msgpack_encode(sender.signer.sign_transactions([txn], [0])[0])
    signed_txn = base64.b64decode(signed_txn)

    # Send the signed transaction using the raw algod_client
    response = algod_client.raw_transaction(signed_txn)
    # Get pending transaction information
    pending_txn = algod_client.pending_transaction_information(txid=response.tx_id)

    # Verify pending transaction response (typed model)
    assert pending_txn.pool_error == ""
    assert pending_txn.confirmed_round is not None
    assert pending_txn.confirmed_round > 0
