import pytest

from algokit_utils import Account
from algokit_utils.account_manager import AddrAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient, PayParams


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client

@pytest.fixture
def bob(algorand: AlgorandClient) -> AddrAndSigner:   
    return algorand.account.random()

def test_send_payment(algorand: AlgorandClient, funded_account: Account, bob: AddrAndSigner):
    alice = funded_account
    amount = 100_000

    alice_pre_balance = algorand.account.get_information(alice.address)['amount']
    bob_pre_balance = algorand.account.get_information(bob.addr)['amount']
    result = algorand.send.payment(PayParams(
        sender=alice.address,
        receiver=bob.addr,
        amount=amount
    ))
    alice_post_balance = algorand.account.get_information(alice.address)['amount']
    bob_post_balance = algorand.account.get_information(bob.addr)['amount']

    assert result['confirmation'] != None
    assert alice_post_balance == alice_pre_balance - 1000 - amount
    assert bob_post_balance == bob_pre_balance + amount