from pathlib import Path
from typing import TYPE_CHECKING

import algokit_utils
import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    CreateCallParameters,
    get_account,
)
from algokit_utils.config import config
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import ApplicationCallTxn, PaymentTxn

from tests.conftest import check_output_stability, get_unique_name

if TYPE_CHECKING:
    from algosdk.abi import Method
    from algosdk.v2client.algod import AlgodClient


@pytest.fixture(scope="module")
def client_fixture(algod_client: "AlgodClient", app_spec: ApplicationSpecification) -> ApplicationClient:
    creator_name = get_unique_name()
    creator = get_account(algod_client, creator_name)
    client = ApplicationClient(algod_client, app_spec, signer=creator)
    create_response = client.create("create")
    assert create_response.tx_id
    return client


def test_app_client_from_app_spec_path(algod_client: "AlgodClient") -> None:
    client = ApplicationClient(algod_client, Path(__file__).parent / "app_client_test.json")

    assert client.app_spec


def test_abi_call_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", name="test")
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"


class PretendSubroutine:
    def __init__(self, method: "Method"):
        self._method = method

    def method_spec(self) -> "Method":
        return self._method


def test_abi_call_with_method_spec(client_fixture: ApplicationClient) -> None:
    hello = client_fixture.app_spec.contract.get_method_by_name("hello")
    subroutine = PretendSubroutine(hello)

    result = client_fixture.call(subroutine, name="test")

    assert result.return_value == "Hello ABI, test"


def test_abi_call_with_transaction_arg(client_fixture: ApplicationClient, funded_account: Account) -> None:
    call_with_payment = client_fixture.app_spec.contract.get_method_by_name("call_with_payment")

    payment = PaymentTxn(
        sender=funded_account.address,
        receiver=client_fixture.app_address,
        amt=1_000_000,
        note=b"Payment",
        sp=client_fixture.algod_client.suggested_params(),
    )  # type: ignore[no-untyped-call]
    payment_with_signer = TransactionWithSigner(payment, AccountTransactionSigner(funded_account.private_key))

    result = client_fixture.call(call_with_payment, payment=payment_with_signer)

    assert result.return_value == "Payment Successful"


def test_abi_call_multiple_times_with_atc(client_fixture: ApplicationClient) -> None:
    atc = AtomicTransactionComposer()
    client_fixture.compose_call(atc, "hello", name="test")
    client_fixture.compose_call(atc, "hello", name="test2")
    client_fixture.compose_call(atc, "hello", name="test3")
    result = atc.execute(client_fixture.algod_client, 4)

    assert result.abi_results[0].return_value == "Hello ABI, test"
    assert result.abi_results[1].return_value == "Hello ABI, test2"
    assert result.abi_results[2].return_value == "Hello ABI, test3"


def test_call_parameters_from_derived_type_ignored(client_fixture: ApplicationClient) -> None:
    client_fixture = client_fixture.prepare()  # make a copy
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


def test_call_with_box(client_fixture: ApplicationClient) -> None:
    algokit_utils.ensure_funded(
        client_fixture.algod_client,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=client_fixture.app_address,
            min_spending_balance_micro_algos=200_000,
            min_funding_increment_micro_algos=200_000,
        ),
    )
    set_response = client_fixture.call(
        "set_box",
        algokit_utils.OnCompleteCallParameters(boxes=[(0, b"ssss")]),
        name=b"ssss",
        value="test",
    )

    assert set_response.confirmed_round

    get_response = client_fixture.call(
        "get_box",
        algokit_utils.OnCompleteCallParameters(boxes=[(0, b"ssss")]),
        name=b"ssss",
    )

    assert get_response.return_value == "test"


def test_call_with_box_readonly(client_fixture: ApplicationClient) -> None:
    algokit_utils.ensure_funded(
        client_fixture.algod_client,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=client_fixture.app_address,
            min_spending_balance_micro_algos=200_000,
            min_funding_increment_micro_algos=200_000,
        ),
    )
    set_response = client_fixture.call(
        "set_box",
        algokit_utils.OnCompleteCallParameters(boxes=[(0, b"ssss")]),
        name=b"ssss",
        value="test",
    )

    assert set_response.confirmed_round

    get_response = client_fixture.call(
        "get_box_readonly",
        algokit_utils.OnCompleteCallParameters(boxes=[(0, b"ssss")]),
        name=b"ssss",
    )

    assert get_response.return_value == "test"


def test_readonly_call(client_fixture: ApplicationClient) -> None:
    response = client_fixture.call(
        "readonly",
        error=0,
    )

    assert response.confirmed_round is None


def test_readonly_call_with_error(client_fixture: ApplicationClient) -> None:
    with pytest.raises(algokit_utils.LogicError) as ex:
        client_fixture.call(
            "readonly",
            error=1,
        )

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))


def test_readonly_call_with_error_with_new_client_provided_template_values(
    algod_client: "AlgodClient",
    funded_account: Account,
) -> None:
    app_spec = Path(__file__).parent / "app_client_test.json"
    client = ApplicationClient(
        algod_client, app_spec, signer=funded_account, template_values={"VERSION": 1, "UPDATABLE": 1, "DELETABLE": 1}
    )
    create_response = client.create("create")
    assert create_response.tx_id

    new_client = ApplicationClient(
        algod_client, app_spec, app_id=client.app_id, signer=funded_account, template_values=client.template_values
    )
    new_client.approval_source_map = client.approval_source_map

    with pytest.raises(algokit_utils.LogicError) as ex:
        new_client.call(
            "readonly",
            error=1,
        )

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))


def test_readonly_call_with_error_with_new_client_provided_source_map(
    algod_client: "AlgodClient",
    funded_account: Account,
) -> None:
    app_spec = Path(__file__).parent / "app_client_test.json"
    client = ApplicationClient(
        algod_client, app_spec, signer=funded_account, template_values={"VERSION": 1, "UPDATABLE": 1, "DELETABLE": 1}
    )
    create_response = client.create("create")
    assert create_response.tx_id

    new_client = ApplicationClient(algod_client, app_spec, app_id=client.app_id, signer=funded_account)
    new_client.approval_source_map = client.approval_source_map

    with pytest.raises(algokit_utils.LogicError) as ex:
        new_client.call(
            "readonly",
            error=1,
        )

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))


def test_readonly_call_with_error_with_imported_source_map(
    algod_client: "AlgodClient",
    funded_account: Account,
) -> None:
    app_spec = Path(__file__).parent / "app_client_test.json"
    client = ApplicationClient(
        algod_client, app_spec, signer=funded_account, template_values={"VERSION": 1, "UPDATABLE": 1, "DELETABLE": 1}
    )
    create_response = client.create("create")
    assert create_response.tx_id
    source_map_export = client.export_source_map()
    assert source_map_export

    new_client = ApplicationClient(algod_client, app_spec, app_id=client.app_id, signer=funded_account)
    new_client.import_source_map(source_map_export)

    with pytest.raises(algokit_utils.LogicError) as ex:
        new_client.call(
            "readonly",
            error=1,
        )

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))


def test_readonly_call_with_error_with_new_client_missing_source_map(
    algod_client: "AlgodClient",
    funded_account: Account,
) -> None:
    app_spec = Path(__file__).parent / "app_client_test.json"
    client = ApplicationClient(
        algod_client, app_spec, signer=funded_account, template_values={"VERSION": 1, "UPDATABLE": 1, "DELETABLE": 1}
    )
    create_response = client.create("create")
    assert create_response.tx_id

    new_client = ApplicationClient(algod_client, app_spec, app_id=client.app_id, signer=funded_account)

    with pytest.raises(algokit_utils.LogicError) as ex:
        new_client.call(
            "readonly",
            error=1,
        )

    check_output_stability(str(ex.value).replace(ex.value.transaction_id, "{txn}"))


def test_readonly_call_with_error_debug_mode_disabled(client_fixture: ApplicationClient) -> None:
    config.configure(debug=False)
    with pytest.raises(algokit_utils.LogicError) as ex:
        client_fixture.call(
            "readonly",
            error=1,
        )
    assert ex.value.traces is None
    config.configure(debug=True)


def test_readonly_call_with_error_debug_mode_enabled(client_fixture: ApplicationClient) -> None:
    with pytest.raises(algokit_utils.LogicError) as ex:
        client_fixture.call(
            "readonly",
            error=1,
        )
    assert ex.value.traces is not None
