import pytest

from algokit_utils import Account
from algokit_utils.account_manager import AddrAndSigner
from algokit_utils.beta.algorand_client import (AlgorandClient,
                                                AssetCreateParams,
                                                AssetOptInParams, PayParams)


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client

@pytest.fixture
def alice(algorand: AlgorandClient, funded_account: Account) -> AddrAndSigner:
    acct = algorand.account.random()
    algorand.send.payment(PayParams(
        sender=funded_account.address,
        receiver=acct.addr,
        amount=1_000_000
    ))   
    return acct

@pytest.fixture
def bob(algorand: AlgorandClient, funded_account: Account) -> AddrAndSigner:
    acct = algorand.account.random()
    algorand.send.payment(PayParams(
        sender=funded_account.address,
        receiver=acct.addr,
        amount=1_000_000
    ))   
    return acct

def test_send_payment(algorand: AlgorandClient, alice: AddrAndSigner, bob: AddrAndSigner):
    amount = 100_000

    alice_pre_balance = algorand.account.get_information(alice.addr)['amount']
    bob_pre_balance = algorand.account.get_information(bob.addr)['amount']
    result = algorand.send.payment(PayParams(
        sender=alice.addr,
        receiver=bob.addr,
        amount=amount
    ))
    alice_post_balance = algorand.account.get_information(alice.addr)['amount']
    bob_post_balance = algorand.account.get_information(bob.addr)['amount']

    assert result['confirmation'] != None
    assert alice_post_balance == alice_pre_balance - 1000 - amount
    assert bob_post_balance == bob_pre_balance + amount

def test_send_asset_create(algorand: AlgorandClient, alice: AddrAndSigner):
    total = 100

    result = algorand.send.asset_create(AssetCreateParams(sender=alice.addr, total=total))
    asset_index = result['confirmation']['asset-index']

    assert asset_index > 0

def test_asset_opt_in(algorand: AlgorandClient, alice: AddrAndSigner, bob: AddrAndSigner):
    total = 100

    result = algorand.send.asset_create(AssetCreateParams(sender=alice.addr, total=total))
    asset_index = result['confirmation']['asset-index']

    result = algorand.send.asset_opt_in(AssetOptInParams(sender=bob.addr, asset_id=asset_index))

    assert algorand.account.get_asset_information(bob.addr, asset_index) != None