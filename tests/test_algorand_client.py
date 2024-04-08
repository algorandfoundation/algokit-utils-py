import pytest

from algokit_utils import Account
from algokit_utils.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import (AlgorandClient,
                                                AssetCreateParams,
                                                AssetOptInParams, PayParams)


@pytest.fixture
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client

@pytest.fixture
def alice(algorand: AlgorandClient, funded_account: Account) -> AddressAndSigner:
    acct = algorand.account.random()
    algorand.send.payment(PayParams(
        sender=funded_account.address,
        receiver=acct.address,
        amount=1_000_000
    ))   
    return acct

@pytest.fixture
def bob(algorand: AlgorandClient, funded_account: Account) -> AddressAndSigner:
    acct = algorand.account.random()
    algorand.send.payment(PayParams(
        sender=funded_account.address,
        receiver=acct.address,
        amount=1_000_000
    ))   
    return acct

def test_send_payment(algorand: AlgorandClient, alice: AddressAndSigner, bob: AddressAndSigner):
    amount = 100_000

    alice_pre_balance = algorand.account.get_information(alice.address)['amount']
    bob_pre_balance = algorand.account.get_information(bob.address)['amount']
    result = algorand.send.payment(PayParams(
        sender=alice.address,
        receiver=bob.address,
        amount=amount
    ))
    alice_post_balance = algorand.account.get_information(alice.address)['amount']
    bob_post_balance = algorand.account.get_information(bob.address)['amount']

    assert result['confirmation'] != None
    assert alice_post_balance == alice_pre_balance - 1000 - amount
    assert bob_post_balance == bob_pre_balance + amount

def test_send_asset_create(algorand: AlgorandClient, alice: AddressAndSigner):
    total = 100

    result = algorand.send.asset_create(AssetCreateParams(sender=alice.address, total=total))
    asset_index = result['confirmation']['asset-index']

    assert asset_index > 0

def test_asset_opt_in(algorand: AlgorandClient, alice: AddressAndSigner, bob: AddressAndSigner):
    total = 100

    result = algorand.send.asset_create(AssetCreateParams(sender=alice.address, total=total))
    asset_index = result['confirmation']['asset-index']

    result = algorand.send.asset_opt_in(AssetOptInParams(sender=bob.address, asset_id=asset_index))

    assert algorand.account.get_asset_information(bob.address, asset_index) != None