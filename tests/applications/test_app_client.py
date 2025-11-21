import base64
import json
import random
from pathlib import Path
from typing import Any

import algosdk
import pytest
from algosdk.atomic_transaction_composer import TransactionSigner, TransactionWithSigner

from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.abi import ABIType
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientMethodCallParams,
    AppClientParams,
    FundAppAccountParams,
)
from algokit_utils.applications.app_factory import AppFactoryCreateMethodCallParams
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.applications.app_spec.arc32 import Arc32Contract
from algokit_utils.applications.app_spec.arc56 import Arc56Contract, Network
from algokit_utils.errors.logic_error import LogicError
from algokit_utils.models.account import SigningAccount
from algokit_utils.models.amount import AlgoAmount, micro_algo
from algokit_utils.models.state import BoxReference
from algokit_utils.transactions.transaction_composer import AppCallMethodCallParams, AppCreateParams, PaymentParams


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> SigningAccount:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algo(100), min_funding_increment=AlgoAmount.from_algo(1)
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


@pytest.fixture
def raw_hello_world_arc32_app_spec() -> str:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "app_spec.arc32.json"
    return raw_json_spec.read_text()


@pytest.fixture
def hello_world_arc32_app_spec() -> Arc56Contract:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "hello_world" / "app_spec.arc32.json"
    return Arc56Contract.from_arc32(raw_json_spec.read_text())


@pytest.fixture
def hello_world_arc32_app_id(
    algorand: AlgorandClient, funded_account: SigningAccount, hello_world_arc32_app_spec: Arc56Contract
) -> int:
    global_schema = hello_world_arc32_app_spec.state.schema.global_state
    local_schema = hello_world_arc32_app_spec.state.schema.local_state
    approval = hello_world_arc32_app_spec.source.get_decoded_approval()
    clear = hello_world_arc32_app_spec.source.get_decoded_clear()
    assert approval is not None, "Approval program must be defined in the app spec"
    assert clear is not None, "Clear state program must be defined in the app spec"
    response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=approval,
            clear_state_program=clear,
            schema={
                "global_ints": int(global_schema.ints) if global_schema.ints else 0,
                "global_byte_slices": int(global_schema.bytes) if global_schema.bytes else 0,
                "local_ints": int(local_schema.ints) if local_schema.ints else 0,
                "local_byte_slices": int(local_schema.bytes) if local_schema.bytes else 0,
            },
        )
    )
    return response.app_id


@pytest.fixture
def raw_testing_app_arc32_app_spec() -> str:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "testing_app" / "app_spec.arc32.json"
    return raw_json_spec.read_text()


@pytest.fixture
def testing_app_arc32_app_spec() -> Arc32Contract:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "testing_app" / "app_spec.arc32.json"
    return Arc32Contract.from_json(raw_json_spec.read_text())


@pytest.fixture
def testing_app_arc32_app_id(
    algorand: AlgorandClient, funded_account: SigningAccount, testing_app_arc32_app_spec: Arc32Contract
) -> int:
    global_schema = testing_app_arc32_app_spec.global_state_schema
    local_schema = testing_app_arc32_app_spec.local_state_schema
    approval = AppManager.replace_template_variables(
        testing_app_arc32_app_spec.approval_program,
        {
            "VALUE": 1,
            "UPDATABLE": 0,
            "DELETABLE": 0,
        },
    )
    response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=approval,
            clear_state_program=testing_app_arc32_app_spec.clear_program,
            schema={
                "global_byte_slices": int(global_schema.num_byte_slices) if global_schema.num_byte_slices else 0,
                "global_ints": int(global_schema.num_uints) if global_schema.num_uints else 0,
                "local_byte_slices": int(local_schema.num_byte_slices) if local_schema.num_byte_slices else 0,
                "local_ints": int(local_schema.num_uints) if local_schema.num_uints else 0,
            },
        )
    )
    return response.app_id


@pytest.fixture
def test_app_client(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
    testing_app_arc32_app_spec: Arc32Contract,
    testing_app_arc32_app_id: int,
) -> AppClient:
    return AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=testing_app_arc32_app_id,
            algorand=algorand,
            app_spec=testing_app_arc32_app_spec,
        )
    )


@pytest.fixture
def test_app_client_with_sourcemaps(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
    testing_app_arc32_app_spec: Arc32Contract,
    testing_app_arc32_app_id: int,
) -> AppClient:
    sourcemaps = json.loads(
        (Path(__file__).parent.parent / "artifacts" / "testing_app" / "sources.teal.map.json").read_text()
    )
    return AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=testing_app_arc32_app_id,
            algorand=algorand,
            approval_source_map=algosdk.source_map.SourceMap(sourcemaps["approvalSourceMap"]),
            clear_source_map=algosdk.source_map.SourceMap(sourcemaps["clearSourceMap"]),
            app_spec=testing_app_arc32_app_spec,
        )
    )


@pytest.fixture
def testing_app_puya_arc32_app_spec() -> Arc32Contract:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "testing_app_puya" / "app_spec.arc32.json"
    return Arc32Contract.from_json(raw_json_spec.read_text())


@pytest.fixture
def testing_app_puya_arc32_app_id(
    algorand: AlgorandClient, funded_account: SigningAccount, testing_app_puya_arc32_app_spec: Arc32Contract
) -> int:
    global_schema = testing_app_puya_arc32_app_spec.global_state_schema
    local_schema = testing_app_puya_arc32_app_spec.local_state_schema

    response = algorand.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
            approval_program=testing_app_puya_arc32_app_spec.approval_program,
            clear_state_program=testing_app_puya_arc32_app_spec.clear_program,
            schema={
                "global_byte_slices": int(global_schema.num_byte_slices) if global_schema.num_byte_slices else 0,
                "global_ints": int(global_schema.num_uints) if global_schema.num_uints else 0,
                "local_byte_slices": int(local_schema.num_byte_slices) if local_schema.num_byte_slices else 0,
                "local_ints": int(local_schema.num_uints) if local_schema.num_uints else 0,
            },
        )
    )
    return response.app_id


@pytest.fixture
def test_app_client_puya(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
    testing_app_puya_arc32_app_spec: Arc32Contract,
    testing_app_puya_arc32_app_id: int,
) -> AppClient:
    return AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=testing_app_puya_arc32_app_id,
            algorand=algorand,
            app_spec=testing_app_puya_arc32_app_spec,
        )
    )


def test_clone_overriding_default_sender_and_inheriting_app_name(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
    hello_world_arc32_app_spec: Arc56Contract,
    hello_world_arc32_app_id: int,
) -> None:
    app_client = AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=hello_world_arc32_app_id,
            algorand=algorand,
            app_spec=hello_world_arc32_app_spec,
        )
    )

    cloned_default_sender = "ABC" * 55
    cloned_app_client = app_client.clone(default_sender=cloned_default_sender)

    assert app_client.app_name == "HelloWorld"
    assert cloned_app_client.app_id == app_client.app_id
    assert cloned_app_client.app_name == app_client.app_name
    assert cloned_app_client._default_sender == cloned_default_sender  # noqa: SLF001
    assert app_client._default_sender == funded_account.address  # noqa: SLF001


def test_clone_overriding_app_name(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
    hello_world_arc32_app_spec: Arc56Contract,
    hello_world_arc32_app_id: int,
) -> None:
    app_client = AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=hello_world_arc32_app_id,
            algorand=algorand,
            app_spec=hello_world_arc32_app_spec,
        )
    )

    cloned_app_name = "George CLONEy"
    cloned_app_client = app_client.clone(app_name=cloned_app_name)
    assert app_client.app_name == hello_world_arc32_app_spec.name == "HelloWorld"
    assert cloned_app_client.app_name == cloned_app_name

    # Test for explicit None when closning
    cloned_app_client = app_client.clone(app_name=None)
    assert cloned_app_client.app_name == app_client.app_name


def test_clone_inheriting_app_name_based_on_default_handling(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
    hello_world_arc32_app_spec: Arc56Contract,
    hello_world_arc32_app_id: int,
) -> None:
    app_client = AppClient(
        AppClientParams(
            default_sender=funded_account.address,
            default_signer=funded_account.signer,
            app_id=hello_world_arc32_app_id,
            algorand=algorand,
            app_spec=hello_world_arc32_app_spec,
        )
    )

    cloned_app_name = None
    cloned_app_client = app_client.clone(app_name=cloned_app_name)
    assert cloned_app_client.app_name == hello_world_arc32_app_spec.name == app_client.app_name


def test_group_simulate_matches_send(
    funded_account: SigningAccount,
    test_app_client: AppClient,
) -> None:
    app_call1_params = AppCallMethodCallParams(
        sender=funded_account.address,
        app_id=test_app_client.app_id,
        method=algosdk.abi.Method.from_signature("set_global(uint64,uint64,string,byte[4])void"),
        args=[1, 2, "asdf", bytes([1, 2, 3, 4])],
    )
    payment_params = PaymentParams(
        sender=funded_account.address, receiver=funded_account.address, amount=micro_algo(10000)
    )
    app_call2_params = AppCallMethodCallParams(
        sender=funded_account.address,
        app_id=test_app_client.app_id,
        method=algosdk.abi.Method.from_signature("call_abi(string)string"),
        args=["test"],
    )

    simulate_result = (
        test_app_client.algorand.new_group()
        .add_app_call_method_call(app_call1_params)
        .add_payment(payment_params)
        .add_app_call_method_call(app_call2_params)
        .simulate(skip_signatures=True)
    )

    send_result = (
        test_app_client.algorand.new_group()
        .add_app_call_method_call(app_call1_params)
        .add_payment(payment_params)
        .add_app_call_method_call(app_call2_params)
        .send()
    )

    assert len(simulate_result.transactions) == len(send_result.transactions)
    assert len(simulate_result.returns) == len(send_result.returns)
    assert simulate_result.returns[0].value == send_result.returns[0].value
    assert simulate_result.returns[1].value == send_result.returns[1].value


def test_normalise_app_spec(
    raw_hello_world_arc32_app_spec: str,
    hello_world_arc32_app_spec: Arc56Contract,
) -> None:
    normalized_app_spec_from_arc32 = AppClient.normalise_app_spec(hello_world_arc32_app_spec)
    assert isinstance(normalized_app_spec_from_arc32, Arc56Contract)

    normalize_app_spec_from_raw_arc32 = AppClient.normalise_app_spec(raw_hello_world_arc32_app_spec)
    assert isinstance(normalize_app_spec_from_raw_arc32, Arc56Contract)


def test_resolve_from_network(
    algorand: AlgorandClient,
    hello_world_arc32_app_id: int,
    hello_world_arc32_app_spec: Arc56Contract,
) -> None:
    arc56_app_spec = hello_world_arc32_app_spec
    arc56_app_spec.networks = {"localnet": Network(app_id=hello_world_arc32_app_id)}
    app_client = AppClient.from_network(
        algorand=algorand,
        app_spec=arc56_app_spec,
    )

    assert app_client


def test_construct_transaction_with_boxes(test_app_client: AppClient) -> None:
    call = test_app_client.create_transaction.call(
        AppClientMethodCallParams(
            method="call_abi",
            args=["test"],
            box_references=[BoxReference(app_id=0, name=b"1")],
        )
    )

    assert isinstance(call.transactions[0], algosdk.transaction.ApplicationCallTxn)
    assert call.transactions[0].boxes == [BoxReference(app_id=0, name=b"1")]  # type: ignore  # noqa: PGH003

    # Test with string box reference
    call2 = test_app_client.create_transaction.call(
        AppClientMethodCallParams(
            method="call_abi",
            args=["test"],
            box_references=["1"],
        )
    )

    assert isinstance(call2.transactions[0], algosdk.transaction.ApplicationCallTxn)
    assert call2.transactions[0].boxes == [BoxReference(app_id=0, name=b"1")]  # type: ignore  # noqa: PGH003


def test_construct_transaction_with_abi_encoding_including_transaction(
    algorand: AlgorandClient, funded_account: SigningAccount, test_app_client: AppClient
) -> None:
    # Create a payment transaction with random amount
    amount = AlgoAmount.from_micro_algo(random.randint(1, 10000))
    payment_txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=amount,
        )
    )

    # Call the ABI method with the payment transaction
    result = test_app_client.send.call(
        AppClientMethodCallParams(
            method="call_abi_txn",
            args=[payment_txn, "test"],
        )
    )

    assert result.confirmation
    assert len(result.transactions) == 2
    response = AppManager.get_abi_return(result.confirmation, test_app_client.app_spec.get_arc56_method("call_abi_txn"))
    expected_return = f"Sent {amount.micro_algo}. test"
    assert result.abi_return == expected_return
    assert response
    assert response.value == result.abi_return


def test_sign_all_transactions_in_group_with_abi_call_with_transaction_arg(
    algorand: AlgorandClient, test_app_client: AppClient, funded_account: SigningAccount
) -> None:
    # Create a payment transaction with a random amount
    amount = AlgoAmount.from_micro_algo(random.randint(1, 10000))
    txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=amount,
        )
    )

    called_indexes = []
    original_signer = algorand.account.get_signer(funded_account.address)

    class IndexCapturingSigner(TransactionSigner):
        def sign_transactions(
            self, txn_group: list[algosdk.transaction.Transaction], indexes: list[int]
        ) -> list[algosdk.transaction.GenericSignedTransaction]:
            called_indexes.extend(indexes)
            return original_signer.sign_transactions(txn_group, indexes)

    test_app_client.send.call(
        AppClientMethodCallParams(
            method="call_abi_txn",
            args=[txn, "test"],
            sender=funded_account.address,
            signer=IndexCapturingSigner(),
        )
    )

    assert set(called_indexes) == {0, 1}


def test_sign_transaction_in_group_with_different_signer_if_provided(
    algorand: AlgorandClient, test_app_client: AppClient, funded_account: SigningAccount
) -> None:
    # Generate a new account
    test_account = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=test_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(10),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    # Fund the account with 1 Algo
    txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=test_account.address,
            receiver=test_account.address,
            amount=AlgoAmount.from_algo(random.randint(1, 5)),
        )
    )

    # Call method with transaction and signer
    test_app_client.send.call(
        AppClientMethodCallParams(
            method="call_abi_txn",
            args=[TransactionWithSigner(txn=txn, signer=test_account.signer), "test"],
        )
    )


def test_construct_transaction_with_abi_encoding_including_foreign_references_not_in_signature(
    algorand: AlgorandClient, test_app_client: AppClient, funded_account: SigningAccount
) -> None:
    test_account = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=test_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(10),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    result = test_app_client.send.call(
        AppClientMethodCallParams(
            method="call_abi_foreign_refs",
            app_references=[345],
            account_references=[test_account.address],
            asset_references=[567],
        )
    )

    # Assuming the method returns a string matching the format below
    expected_return = AppManager.get_abi_return(
        result.confirmations[0], test_app_client.app_spec.get_arc56_method("call_abi_foreign_refs")
    )
    assert result.abi_return
    assert str(result.abi_return).startswith("App: 345, Asset: 567, Account: ")
    assert expected_return
    assert expected_return.value == result.abi_return


def test_retrieve_state(test_app_client: AppClient, funded_account: SigningAccount) -> None:
    # Test global state
    test_app_client.send.call(AppClientMethodCallParams(method="set_global", args=[1, 2, "asdf", bytes([1, 2, 3, 4])]))
    global_state = test_app_client.get_global_state()

    assert "int1" in global_state
    assert "int2" in global_state
    assert "bytes1" in global_state
    assert "bytes2" in global_state
    assert hasattr(global_state["bytes2"], "value_raw")
    assert sorted(global_state.keys()) == ["bytes1", "bytes2", "int1", "int2", "value"]
    assert global_state["int1"].value == 1
    assert global_state["int2"].value == 2
    assert global_state["bytes1"].value == "asdf"
    assert global_state["bytes2"].value_raw == bytes([1, 2, 3, 4])

    # Test local state
    test_app_client.send.opt_in(AppClientMethodCallParams(method="opt_in"))
    test_app_client.send.call(AppClientMethodCallParams(method="set_local", args=[1, 2, "asdf", bytes([1, 2, 3, 4])]))
    local_state = test_app_client.get_local_state(funded_account.address)

    assert "local_int1" in local_state
    assert "local_int2" in local_state
    assert "local_bytes1" in local_state
    assert "local_bytes2" in local_state
    assert sorted(local_state.keys()) == ["local_bytes1", "local_bytes2", "local_int1", "local_int2"]
    assert local_state["local_int1"].value == 1
    assert local_state["local_int2"].value == 2
    assert local_state["local_bytes1"].value == "asdf"
    assert local_state["local_bytes2"].value_raw == bytes([1, 2, 3, 4])

    # Test box storage
    box_name1 = bytes([0, 0, 0, 1])
    box_name1_base64 = base64.b64encode(box_name1).decode()
    box_name2 = bytes([0, 0, 0, 2])
    box_name2_base64 = base64.b64encode(box_name2).decode()

    test_app_client.fund_app_account(params=FundAppAccountParams(amount=AlgoAmount.from_algo(1)))

    test_app_client.send.call(
        AppClientMethodCallParams(
            method="set_box",
            args=[box_name1, "value1"],
            box_references=[box_name1],
        )
    )
    test_app_client.send.call(
        AppClientMethodCallParams(
            method="set_box",
            args=[box_name2, "value2"],
            box_references=[box_name2],
        )
    )

    box_values = test_app_client.get_box_values()
    box1_value = test_app_client.get_box_value(box_name1)

    assert sorted(b.name.name_base64 for b in box_values) == sorted([box_name1_base64, box_name2_base64])
    box1 = next(b for b in box_values if b.name.name_base64 == box_name1_base64)
    assert box1.value == b"value1"
    assert box1_value == box1.value

    box2 = next(b for b in box_values if b.name.name_base64 == box_name2_base64)
    assert box2.value == b"value2"

    # Legacy contract strips ABI prefix; manually encoded ABI string after
    # passing algosdk's atc results in \x00\n\x00\n1234524352.
    expected_value_decoded = "1234524352"
    expected_value = "\x00\n" + expected_value_decoded
    test_app_client.send.call(
        AppClientMethodCallParams(
            method="set_box",
            args=[box_name1, expected_value],
            box_references=[box_name1],
        )
    )

    boxes = test_app_client.get_box_values_from_abi_type(
        ABIType.from_string("string"),
        lambda n: n.name_base64 == box_name1_base64,
    )
    box1_abi_value = test_app_client.get_box_value_from_abi_type(box_name1, ABIType.from_string("string"))

    assert len(boxes) == 1
    assert boxes[0].value == expected_value_decoded
    assert box1_abi_value == expected_value_decoded


@pytest.mark.parametrize(
    ("box_name", "box_value", "value_type", "expected_value"),
    [
        (
            "name1",
            b"test_bytes",  # Updated to match Bytes type
            "byte[]",
            b"test_bytes",
        ),
        (
            "name2",
            "test_string",
            "string",
            "test_string",
        ),
        (
            "name3",  # Updated to use string key
            123,
            "uint32",
            123,
        ),
        (
            "name4",  # Updated to use string key
            2**256,  # Large number within uint512 range
            "uint512",
            2**256,
        ),
        (
            "name5",  # Updated to use string key
            bytes([1, 2, 3, 4]),
            "byte[4]",
            bytes([1, 2, 3, 4]),
        ),
    ],
)
def test_box_methods_with_manually_encoded_abi_args(
    test_app_client_puya: AppClient,
    box_name: Any,  # noqa: ANN401
    box_value: Any,  # noqa: ANN401
    value_type: str,
    expected_value: Any,  # noqa: ANN401
) -> None:
    # Fund the app account
    box_prefix = b"box_bytes"

    test_app_client_puya.fund_app_account(params=FundAppAccountParams(amount=AlgoAmount.from_algo(1)))

    # Encode the box reference
    box_identifier = box_prefix + ABIType.from_string("string").encode(box_name)

    # Call the method to set the box value
    test_app_client_puya.send.call(
        AppClientMethodCallParams(
            method="set_box_bytes",
            args=[box_name, ABIType.from_string(value_type).encode(box_value)],
            box_references=[box_identifier],
        )
    )

    # Get and verify the box value
    box_abi_value = test_app_client_puya.get_box_value_from_abi_type(box_identifier, ABIType.from_string(value_type))

    # Convert the retrieved value to match expected type if needed
    assert box_abi_value == expected_value


@pytest.mark.parametrize(
    ("box_prefix_str", "method", "arg_value", "value_type"),
    [
        ("box_str", "set_box_str", "string", "string"),
        ("box_int", "set_box_int", 123, "uint32"),
        ("box_int512", "set_box_int512", 2**256, "uint512"),
        ("box_static", "set_box_static", bytes([1, 2, 3, 4]), "byte[4]"),
        ("", "set_struct", ("box1", 123), "(string,uint64)"),
    ],
)
def test_box_methods_with_arc4_returns_parametrized(
    test_app_client_puya: AppClient,
    box_prefix_str: str,
    method: str,
    arg_value: Any,  # noqa: ANN401
    value_type: str,
) -> None:
    # Encode the box prefix
    box_prefix = box_prefix_str.encode()

    # Fund the app account with 1 Algo
    test_app_client_puya.fund_app_account(params=FundAppAccountParams(amount=AlgoAmount.from_algo(1)))

    # Encode the box name "box1" using ABIType "string"
    box_name_encoded = ABIType.from_string("string").encode("box1")
    box_reference = box_prefix + box_name_encoded

    # Send the transaction to set the box value
    test_app_client_puya.send.call(
        AppClientMethodCallParams(
            method=method,
            args=["box1", arg_value],
            box_references=[box_reference],
        )
    )

    # Encode the expected value using the specified ABI type
    expected_value = ABIType.from_string(value_type).encode(arg_value)

    # Retrieve the actual box value
    actual_box_value = test_app_client_puya.get_box_value(box_reference)

    # Assert that the actual box value matches the expected value
    assert actual_box_value == expected_value

    if method == "set_struct":
        abi_decoded_boxes = test_app_client_puya.get_box_values_from_abi_type(
            ABIType.from_string("(string,uint64)"),
            lambda n: n.name_base64 == base64.b64encode(box_prefix + box_name_encoded).decode(),
        )
        assert len(abi_decoded_boxes) == 1
        assert abi_decoded_boxes[0].value == arg_value


def test_abi_with_default_arg_method(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
    testing_app_arc32_app_id: int,
    testing_app_arc32_app_spec: Arc32Contract,
) -> None:
    arc56_app_spec = Arc56Contract.from_arc32(testing_app_arc32_app_spec)
    arc56_app_spec.networks = {"localnet": Network(app_id=testing_app_arc32_app_id)}
    app_client = AppClient.from_network(
        algorand=algorand,
        app_spec=arc56_app_spec,
        default_sender=funded_account.address,
        default_signer=funded_account.signer,
    )
    # app_client.send.
    app_client.send.opt_in(AppClientMethodCallParams(method="opt_in"))
    app_client.send.call(
        AppClientMethodCallParams(
            method="set_local",
            args=[1, 2, "banana", [1, 2, 3, 4]],
        )
    )

    method_signature = "default_value_from_local_state(string)string"
    defined_value = "defined value"

    # Test with defined value
    defined_value_result = app_client.send.call(
        AppClientMethodCallParams(method=method_signature, args=[defined_value])
    )

    assert defined_value_result.abi_return == "Local state, defined value"

    # Test with default value
    default_value_result = app_client.send.call(AppClientMethodCallParams(method=method_signature, args=[None]))
    assert default_value_result
    assert default_value_result.abi_return == "Local state, banana"


def test_exposing_logic_error(test_app_client_with_sourcemaps: AppClient) -> None:
    with pytest.raises(LogicError) as exc_info:
        test_app_client_with_sourcemaps.send.call(AppClientMethodCallParams(method="error"))

    error = exc_info.value
    assert error.pc == 885
    assert "assert failed pc=885" in str(error)
    assert len(error.transaction_id) == 52
    assert error.line_no == 469


@pytest.fixture
def nested_struct_app_spec() -> Arc56Contract:
    raw_json_spec = Path(__file__).parent.parent / "artifacts" / "nested_struct" / "nested_struct.arc56.json"
    return Arc56Contract.from_json(raw_json_spec.read_text())


def test_nested_structs_described_by_structure(
    algorand: AlgorandClient, funded_account: SigningAccount, nested_struct_app_spec: Arc56Contract
) -> None:
    """Test nested struct when described by structure."""
    factory = algorand.client.get_app_factory(app_spec=nested_struct_app_spec, default_sender=funded_account.address)
    app_client, _ = factory.send.create(AppFactoryCreateMethodCallParams(method="createApplication", args=[]))
    app_client.send.call(AppClientMethodCallParams(method="setValue", args=[1, "hello"]))

    result = app_client.send.call(AppClientMethodCallParams(method="getValue", args=[1]))

    assert result.abi_return == {"x": {"a": "hello"}}


def test_app_client_error_transformer_logic_error_enhancement(test_app_client_with_sourcemaps: AppClient) -> None:
    """Test that AppClient error transformers enhance logic errors with source maps."""
    with pytest.raises(LogicError) as exc_info:
        test_app_client_with_sourcemaps.send.call(AppClientMethodCallParams(method="error"))

    error = exc_info.value
    # Verify the error was enhanced by the error transformer
    assert error.pc == 885
    assert "assert failed pc=885" in str(error)
    assert len(error.transaction_id) == 52
    assert error.line_no == 469
    # This should be a LogicError, which means the error transformer processed it
    assert isinstance(error, LogicError)


def test_nested_structs_referenced_by_name(
    algorand: AlgorandClient, funded_account: SigningAccount, nested_struct_app_spec: Arc56Contract
) -> None:
    """Test nested struct when referenced by name."""
    edited_spec_dict = nested_struct_app_spec.dictify()
    edited_spec_dict["structs"] = {
        "Struct1": [
            {
                "name": "a",
                "type": "string",
            }
        ],
        "Struct2": [
            {
                "name": "x",
                "type": "Struct1",
            }
        ],
    }
    edited_spec = Arc56Contract.from_json(json.dumps(edited_spec_dict))
    factory = algorand.client.get_app_factory(app_spec=edited_spec, default_sender=funded_account.address)
    app_client, _ = factory.send.create(AppFactoryCreateMethodCallParams(method="createApplication", args=[]))
    app_client.send.call(AppClientMethodCallParams(method="setValue", args=[1, "hello"]))

    result = app_client.send.call(AppClientMethodCallParams(method="getValue", args=[1]))

    assert result.abi_return == {"x": {"a": "hello"}}
