from __future__ import annotations

import base64

from algosdk import encoding, transaction

from algokit_algod_client import AlgodClient
from algokit_utils import SigningAccount
from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.amount import AlgoAmount


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

    params = algorand.client.algod.suggested_params()
    txn = transaction.PaymentTxn(
        sender=sender.address,
        sp=params,
        receiver=receiver.address,
        amt=500_000,
        note=b"Test payment transaction",
    )

    signed_txn = encoding.msgpack_encode(sender.signer.sign_transactions([txn], [0])[0])
    signed_bytes = base64.b64decode(signed_txn)

    res = algod_client.raw_transaction(body=signed_bytes)
    assert isinstance(res.tx_id, str)
    assert res.tx_id
