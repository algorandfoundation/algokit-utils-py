import json
from pathlib import Path

import pytest
from algokit_utils import Account, ApplicationClient
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
    AssetCreateParams,
    AssetOptInParams,
    MethodCallParams,
    PayParams,
)
from algosdk.abi import Contract
from algosdk.atomic_transaction_composer import AtomicTransactionComposer


@pytest.fixture()
def algorand(funded_account: Account) -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_signer(sender=funded_account.address, signer=funded_account.signer)
    return client

@pytest.fixture()
def alice(algorand: AlgorandClient, funded_account: Account) -> AddressAndSigner:
    acct = algorand.account.random()
    algorand.send.payment(PayParams(
        sender=funded_account.address,
        receiver=acct.address,
        amount=1_000_000
    ))
    return acct

@pytest.fixture()
def bob(algorand: AlgorandClient, funded_account: Account) -> AddressAndSigner:
    acct = algorand.account.random()
    algorand.send.payment(PayParams(
        sender=funded_account.address,
        receiver=acct.address,
        amount=1_000_000
    ))
    return acct

@pytest.fixture()
def app_client(algorand: AlgorandClient, alice: AddressAndSigner) -> ApplicationClient:
    client = ApplicationClient(algorand.client.algod, Path(__file__).parent / "app_algorand_client.json", sender=alice.address, signer=alice.signer)
    client.create(call_abi_method='createApplication')
    return client

@pytest.fixture()
def contract():
    with open(Path(__file__).parent / "app_algorand_client.json") as f:
        return Contract.from_json(json.dumps(json.load(f)['contract']))


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

    assert result['confirmation'] is not None
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

    assert algorand.account.get_asset_information(bob.address, asset_index) is not None

def test_add_atc(algorand: AlgorandClient, app_client: ApplicationClient, alice: AddressAndSigner):
    atc = AtomicTransactionComposer()
    atc.add_method_call
    app_client.compose_call(atc, call_abi_method='doMath', a=1, b=2, operation='sum')

    result = algorand.new_group().add_payment(PayParams(sender=alice.address, amount=0, receiver=alice.address)).add_atc(atc).execute()
    assert result.abi_results[0].return_value == 3

def test_add_method_call(algorand: AlgorandClient, contract: Contract, alice: AddressAndSigner, app_client: ApplicationClient):
    result = algorand \
        .new_group() \
        .add_payment(PayParams(sender=alice.address, amount=0, receiver=alice.address)) \
        .add_method_call(MethodCallParams(method=contract.get_method_by_name('doMath'), sender=alice.address, app_id=app_client.app_id, args=[1,2,'sum'])) \
        .execute()
    assert result.abi_results[0].return_value == 3

def test_add_method_with_txn_arg(algorand: AlgorandClient, contract: Contract, alice: AddressAndSigner, app_client: ApplicationClient):
    pay_arg = PayParams(sender=alice.address, receiver=alice.address, amount=1)
    result = algorand \
        .new_group() \
        .add_payment(PayParams(sender=alice.address, amount=0, receiver=alice.address)) \
        .add_method_call(MethodCallParams(method=contract.get_method_by_name('txnArg'), sender=alice.address, app_id=app_client.app_id, args=[pay_arg])) \
        .execute()
    assert result.abi_results[0].return_value == alice.address

def test_add_method_call_with_method_call_arg(algorand: AlgorandClient, contract: Contract, alice: AddressAndSigner, app_client: ApplicationClient):
    hello_world_call = MethodCallParams(method=contract.get_method_by_name('helloWorld'), sender=alice.address, app_id=app_client.app_id)
    result = algorand \
        .new_group() \
        .add_method_call(MethodCallParams(method=contract.get_method_by_name('methodArg'), sender=alice.address, app_id=app_client.app_id, args=[hello_world_call])) \
        .execute()
    assert result.abi_results[0].return_value == 'Hello, World!'
    assert result.abi_results[1].return_value == app_client.app_id


def test_add_method_call_with_method_call_arg_with_txn_arg(algorand: AlgorandClient, contract: Contract, alice: AddressAndSigner, app_client: ApplicationClient):
    pay_arg = PayParams(sender=alice.address, receiver=alice.address, amount=1)
    txn_arg_call = MethodCallParams(method=contract.get_method_by_name('txnArg'), sender=alice.address, app_id=app_client.app_id, args=[pay_arg])
    result = algorand \
        .new_group() \
        .add_method_call(MethodCallParams(method=contract.get_method_by_name('nestedTxnArg'), sender=alice.address, app_id=app_client.app_id, args=[txn_arg_call])) \
        .execute()
    assert result.abi_results[0].return_value == alice.address
    assert result.abi_results[1].return_value == app_client.app_id

def test_add_method_call_with_two_method_call_args_with_txn_arg(algorand: AlgorandClient, contract: Contract, alice: AddressAndSigner, app_client: ApplicationClient):
    pay_arg_1 = PayParams(sender=alice.address, receiver=alice.address, amount=1)
    txn_arg_call_1 = MethodCallParams(method=contract.get_method_by_name('txnArg'), sender=alice.address, app_id=app_client.app_id, args=[pay_arg_1], note=b'1')

    pay_arg_2 = PayParams(sender=alice.address, receiver=alice.address, amount=2)
    txn_arg_call_2 = MethodCallParams(method=contract.get_method_by_name('txnArg'), sender=alice.address, app_id=app_client.app_id, args=[pay_arg_2])

    result = algorand \
        .new_group() \
        .add_method_call(MethodCallParams(method=contract.get_method_by_name('doubleNestedTxnArg'), sender=alice.address, app_id=app_client.app_id, args=[txn_arg_call_1, txn_arg_call_2])) \
        .execute()
    assert result.abi_results[0].return_value == alice.address
    assert result.abi_results[1].return_value == alice.address
    assert result.abi_results[2].return_value == app_client.app_id
