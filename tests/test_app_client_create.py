import dataclasses
from typing import TYPE_CHECKING

import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    CreateCallParameters,
    get_account,
    get_app_id_from_tx_id,
)
from algosdk.atomic_transaction_composer import AccountTransactionSigner, AtomicTransactionComposer, TransactionSigner
from algosdk.transaction import ApplicationCallTxn, GenericSignedTransaction, OnComplete, Transaction

from tests.conftest import check_output_stability, get_unique_name

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient


@pytest.fixture(scope="module")
def client_fixture(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    app_spec: ApplicationSpecification,
    funded_account: Account,
) -> ApplicationClient:
    return ApplicationClient(algod_client, app_spec, creator=funded_account, indexer_client=indexer_client)


def test_bare_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create(call_abi_method=False)

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"


def test_abi_create(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


@pytest.mark.parametrize("method", ["create_args", "create_args(string)void", True])
def test_abi_create_args(method: str | bool, client_fixture: ApplicationClient) -> None:
    client_fixture.create(method, greeting="ahoy")

    assert client_fixture.call("hello", name="test").return_value == "ahoy, test"


def test_create_auto_find(client_fixture: ApplicationClient) -> None:
    client_fixture.create(transaction_parameters=CreateCallParameters(on_complete=OnComplete.OptInOC))

    assert client_fixture.call("hello", name="test").return_value == "Opt In, test"


def test_create_auto_find_ambiguous(client_fixture: ApplicationClient) -> None:
    with pytest.raises(Exception, match="Could not find an exact method to use") as ex:
        client_fixture.create()
    check_output_stability(str(ex.value))


def test_abi_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create")

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", name="test").return_value == "Hello ABI, test"


def test_bare_create_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, call_abi_method=False)

    create_result = atc.execute(client_fixture.algod_client, 4)
    client_fixture.app_id = get_app_id_from_tx_id(client_fixture.algod_client, create_result.tx_ids[0])

    assert client_fixture.call("hello", name="test").return_value == "Hello Bare, test"


def test_create_parameters_lease(client_fixture: ApplicationClient) -> None:
    lease = b"a" * 32

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(
        atc,
        "create",
        transaction_parameters=CreateCallParameters(
            lease=lease,
        ),
    )

    signed_txn = atc.txn_list[0]
    assert signed_txn.txn.lease == lease


def test_create_parameters_note(client_fixture: ApplicationClient) -> None:
    note = b"test note"

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(
        atc,
        "create",
        transaction_parameters=CreateCallParameters(
            note=note,
        ),
    )

    signed_txn = atc.txn_list[0]
    assert signed_txn.txn.note == note


def test_create_parameters_on_complete(client_fixture: ApplicationClient) -> None:
    on_complete = OnComplete.OptInOC

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(
        atc, "create", transaction_parameters=CreateCallParameters(on_complete=OnComplete.OptInOC)
    )

    signed_txn = atc.txn_list[0]
    app_txn = signed_txn.txn
    assert isinstance(app_txn, ApplicationCallTxn)
    assert app_txn.on_complete == on_complete


def test_create_parameters_extra_pages(client_fixture: ApplicationClient) -> None:
    extra_pages = 1

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(extra_pages=extra_pages))

    signed_txn = atc.txn_list[0]
    app_txn = signed_txn.txn
    assert isinstance(app_txn, ApplicationCallTxn)
    assert app_txn.extra_pages == extra_pages


def test_create_parameters_signer(client_fixture: ApplicationClient) -> None:
    another_account_name = get_unique_name()
    account = get_account(client_fixture.algod_client, another_account_name)
    signer = AccountTransactionSigner(account.private_key)

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(signer=signer))

    signed_txn = atc.txn_list[0]
    assert isinstance(signed_txn.signer, AccountTransactionSigner)
    assert signed_txn.signer.private_key == signer.private_key


@dataclasses.dataclass
class DataclassTransactionSigner(TransactionSigner):
    def sign_transactions(self, txn_group: list[Transaction], indexes: list[int]) -> list[GenericSignedTransaction]:
        return self.transaction_signer.sign_transactions(txn_group, indexes)

    transaction_signer: TransactionSigner


def test_create_parameters_dataclass_signer(client_fixture: ApplicationClient) -> None:
    another_account_name = get_unique_name()
    account = get_account(client_fixture.algod_client, another_account_name)
    signer = DataclassTransactionSigner(AccountTransactionSigner(account.private_key))

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(signer=signer))

    signed_txn = atc.txn_list[0]
    assert isinstance(signed_txn.signer, DataclassTransactionSigner)


def test_create_parameters_sender(client_fixture: ApplicationClient) -> None:
    another_account_name = get_unique_name()
    account = get_account(client_fixture.algod_client, another_account_name)

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(sender=account.address))

    signed_txn = atc.txn_list[0]
    assert signed_txn.txn.sender == account.address


def test_create_parameters_rekey_to(client_fixture: ApplicationClient) -> None:
    another_account_name = get_unique_name()
    account = get_account(client_fixture.algod_client, another_account_name)

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(rekey_to=account.address))

    signed_txn = atc.txn_list[0]
    assert signed_txn.txn.rekey_to == account.address


def test_create_parameters_suggested_params(client_fixture: ApplicationClient) -> None:
    sp = client_fixture.algod_client.suggested_params()
    sp.gen = "test-genesis"

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(suggested_params=sp))

    signed_txn = atc.txn_list[0]
    assert signed_txn.txn.genesis_id == sp.gen


def test_create_parameters_boxes(client_fixture: ApplicationClient) -> None:
    boxes = [(0, b"one"), (0, b"two")]

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(boxes=boxes))

    signed_txn = atc.txn_list[0]
    assert isinstance(signed_txn.txn, ApplicationCallTxn)
    assert [(b.app_index, b.name) for b in signed_txn.txn.boxes] == boxes


def test_create_parameters_accounts(client_fixture: ApplicationClient) -> None:
    another_account_name = get_unique_name()
    account = get_account(client_fixture.algod_client, another_account_name)

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(
        atc, "create", transaction_parameters=CreateCallParameters(accounts=[account.address])
    )

    signed_txn = atc.txn_list[0]
    assert isinstance(signed_txn.txn, ApplicationCallTxn)
    assert signed_txn.txn.accounts == [account.address]


def test_create_parameters_foreign_apps(client_fixture: ApplicationClient) -> None:
    foreign_apps = [1, 2, 3]

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(foreign_apps=foreign_apps))

    signed_txn = atc.txn_list[0]
    assert isinstance(signed_txn.txn, ApplicationCallTxn)
    assert signed_txn.txn.foreign_apps == foreign_apps


def test_create_parameters_foreign_assets(client_fixture: ApplicationClient) -> None:
    foreign_assets = [10, 20, 30]

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(
        atc, "create", transaction_parameters=CreateCallParameters(foreign_assets=foreign_assets)
    )

    signed_txn = atc.txn_list[0]
    assert isinstance(signed_txn.txn, ApplicationCallTxn)
    assert signed_txn.txn.foreign_assets == foreign_assets
