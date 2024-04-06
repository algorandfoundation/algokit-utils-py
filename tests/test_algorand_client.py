import pytest

from algokit_utils import Account
from algokit_utils.algorand_client import AlgorandClient, PayTxnParams


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client

def test_send_payment(algorand: AlgorandClient, funded_account: Account):
    result = algorand.send.payment(PayTxnParams(
        sender=funded_account.address,
        receiver=funded_account.address,
        amount=0
    ))

    assert result['confirmation'] != None