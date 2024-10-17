import json
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from algokit_utils._debugging import (
    PersistSourceMapInput,
    persist_sourcemaps,
    simulate_and_persist_response,
)
from algokit_utils.account import get_account
from algokit_utils.application_client import ApplicationClient
from algokit_utils.application_specification import ApplicationSpecification
from algokit_utils.common import Program
from algokit_utils.models import Account
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import PaymentTxn

from tests.conftest import get_unique_name

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


@pytest.fixture()
def client_fixture(algod_client: "AlgodClient", app_spec: ApplicationSpecification) -> ApplicationClient:
    creator_name = get_unique_name()
    creator = get_account(algod_client, creator_name)
    client = ApplicationClient(algod_client, app_spec, signer=creator)
    create_response = client.create("create")
    assert create_response.tx_id
    return client


def test_build_teal_sourcemaps(algod_client: "AlgodClient", tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    approval = """
#pragma version 9
int 1
"""
    clear = """
#pragma version 9
int 1
"""
    sources = [
        PersistSourceMapInput(raw_teal=approval, app_name="cool_app", file_name="approval.teal"),
        PersistSourceMapInput(raw_teal=clear, app_name="cool_app", file_name="clear"),
    ]

    persist_sourcemaps(sources=sources, project_root=cwd, client=algod_client)

    root_path = cwd / ".algokit" / "sources"
    sourcemap_file_path = root_path / "sources.avm.json"
    app_output_path = root_path / "cool_app"

    assert not (sourcemap_file_path).exists()
    assert (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.teal.map").exists()
    assert (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.teal.map").exists()


def test_build_teal_sourcemaps_without_sources(
    algod_client: "AlgodClient", tmp_path_factory: pytest.TempPathFactory
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    approval = """
#pragma version 9
int 1
"""
    clear = """
#pragma version 9
int 1
"""
    compiled_approval = Program(approval, algod_client)
    compiled_clear = Program(clear, algod_client)
    sources = [
        PersistSourceMapInput(compiled_teal=compiled_approval, app_name="cool_app", file_name="approval.teal"),
        PersistSourceMapInput(compiled_teal=compiled_clear, app_name="cool_app", file_name="clear"),
    ]

    persist_sourcemaps(sources=sources, project_root=cwd, client=algod_client, with_sources=False)

    root_path = cwd / ".algokit" / "sources"
    sourcemap_file_path = root_path / "sources.avm.json"
    app_output_path = root_path / "cool_app"

    assert not (sourcemap_file_path).exists()
    assert not (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.teal.map").exists()
    assert json.loads((app_output_path / "approval.teal.map").read_text())["sources"] == []
    assert not (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.teal.map").exists()
    assert json.loads((app_output_path / "clear.teal.map").read_text())["sources"] == []


def test_simulate_and_persist_response_via_app_call(
    tmp_path_factory: pytest.TempPathFactory,
    client_fixture: ApplicationClient,
    mocker: Mock,
) -> None:
    mock_config = mocker.patch("algokit_utils.application_client.config")
    mock_config.debug = True
    mock_config.trace_all = True
    mock_config.trace_buffer_size_mb = 256
    cwd = tmp_path_factory.mktemp("cwd")
    mock_config.project_root = cwd

    client_fixture.call("hello", name="test")

    output_path = cwd / "debug_traces"

    content = list(output_path.iterdir())
    assert len(list(output_path.iterdir())) == 1
    trace_file_content = json.loads(content[0].read_text())
    simulated_txn = trace_file_content["txn-groups"][0]["txn-results"][0]["txn-result"]["txn"]["txn"]
    assert simulated_txn["type"] == "appl"
    assert simulated_txn["apid"] == client_fixture.app_id


def test_simulate_and_persist_response(
    tmp_path_factory: pytest.TempPathFactory, client_fixture: ApplicationClient, mocker: Mock, funded_account: Account
) -> None:
    mock_config = mocker.patch("algokit_utils.application_client.config")
    mock_config.debug = True
    mock_config.trace_all = True
    cwd = tmp_path_factory.mktemp("cwd")
    mock_config.project_root = cwd

    payment = PaymentTxn(
        sender=funded_account.address,
        receiver=client_fixture.app_address,
        amt=1_000_000,
        note=b"Payment",
        sp=client_fixture.algod_client.suggested_params(),
    )  # type: ignore[no-untyped-call]
    txn_with_signer = TransactionWithSigner(payment, AccountTransactionSigner(funded_account.private_key))
    atc = AtomicTransactionComposer()
    atc.add_transaction(txn_with_signer)

    simulate_and_persist_response(atc, cwd, client_fixture.algod_client)

    output_path = cwd / "debug_traces"
    content = list(output_path.iterdir())
    assert len(list(output_path.iterdir())) == 1
    trace_file_content = json.loads(content[0].read_text())
    simulated_txn = trace_file_content["txn-groups"][0]["txn-results"][0]["txn-result"]["txn"]["txn"]
    assert simulated_txn["type"] == "pay"

    trace_file_path = content[0]
    while trace_file_path.exists():
        tmp_atc = atc.clone()
        simulate_and_persist_response(tmp_atc, cwd, client_fixture.algod_client, buffer_size_mb=0.01)
