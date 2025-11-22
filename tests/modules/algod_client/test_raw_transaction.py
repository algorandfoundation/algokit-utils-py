from algokit_algod_client import AlgodClient
from algokit_utils import SigningAccount
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams


def test_raw_transaction_broadcast(algod_client: AlgodClient) -> None:
    algorand = AlgorandClient.default_localnet()
    sender: SigningAccount = algorand.account.random()
    receiver: SigningAccount = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        sender, dispenser, AlgoAmount.from_algo(10), min_funding_increment=AlgoAmount.from_algo(1)
    )
    algorand.account.ensure_funded(
        receiver, dispenser, AlgoAmount.from_algo(1), min_funding_increment=AlgoAmount.from_algo(1)
    )

    txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=AlgoAmount.from_micro_algo(500_000),
            note=b"Test payment transaction",
        )
    )

    signed_blob = sender.signer([txn], [0])[0]

    res = algod_client.send_raw_transaction(signed_blob)
    assert isinstance(res.tx_id, str)
    assert res.tx_id
