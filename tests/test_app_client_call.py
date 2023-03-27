from algokit_utils import (
    ApplicationClient,
    CreateCallParameters,
)
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algosdk.transaction import ApplicationCallTxn


def test_abi_call_with_atc(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", name="test")
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"


def test_abi_call_multiple_times_with_atc(client_fixture: ApplicationClient) -> None:
    client_fixture.create("create")
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", name="test")
    client_fixture.compose_call(atc, "hello", name="test2")
    client_fixture.compose_call(atc, "hello", name="test3")
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"
    assert result.abi_results[1].return_value == "Hello ABI, test2"
    assert result.abi_results[2].return_value == "Hello ABI, test3"


def test_call_parameters_from_derived_type_ignored(client_fixture: ApplicationClient) -> None:
    parameters = CreateCallParameters(
        extra_pages=1,
    )

    client_fixture.app_id = 123
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", transaction_parameters=parameters, name="test")

    signed_txn = atc.txn_list[0]
    app_txn = signed_txn.txn
    assert isinstance(app_txn, ApplicationCallTxn)
    assert app_txn.extra_pages == 0


def test_create_parameters_extra_pages(client_fixture: ApplicationClient) -> None:
    extra_pages = 1

    atc = AtomicTransactionComposer()
    client_fixture.compose_create(atc, "create", transaction_parameters=CreateCallParameters(extra_pages=extra_pages))

    signed_txn = atc.txn_list[0]
    app_txn = signed_txn.txn
    assert isinstance(app_txn, ApplicationCallTxn)
    assert app_txn.extra_pages == extra_pages
