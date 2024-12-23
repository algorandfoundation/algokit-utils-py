import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import PaymentTxn

from algokit_utils._debugging import (
    AVMDebuggerSourceMap,
    PersistSourceMapInput,
    persist_sourcemaps,
    simulate_and_persist_response,
)
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientMethodCallWithSendParams,
)
from algokit_utils.applications.app_factory import AppFactoryCreateMethodCallParams
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.common import Program
from algokit_utils.models.account import Account
from algokit_utils.models.amount import AlgoAmount
from tests.conftest import check_output_stability


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> Account:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account,
        dispenser,
        min_spending_balance=AlgoAmount.from_micro_algos(1_000_000),
        min_funding_increment=AlgoAmount.from_micro_algos(1_000_000),
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


@pytest.fixture
def client_fixture(algorand: AlgorandClient, funded_account: Account) -> AppClient:
    app_spec = (Path(__file__).parent / "artifacts" / "legacy_app_client_test" / "app_client_test.json").read_text()
    app_factory = algorand.client.get_app_factory(
        app_spec=app_spec, default_sender=funded_account.address, default_signer=funded_account.signer
    )
    app_client, _ = app_factory.send.create(
        AppFactoryCreateMethodCallParams(
            method="create", deletable=True, updatable=True, deploy_time_params={"VERSION": 1}
        )
    )
    return app_client


@pytest.fixture
def mock_config() -> Generator[Mock, None, None]:
    with patch("algokit_utils.transactions.transaction_composer.config", new_callable=Mock) as mock_config:
        mock_config.debug = True
        mock_config.project_root = None
        yield mock_config


def test_build_teal_sourcemaps(algorand: AlgorandClient, tmp_path_factory: pytest.TempPathFactory) -> None:
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

    persist_sourcemaps(sources=sources, project_root=cwd, client=algorand.client.algod)

    root_path = cwd / ".algokit" / "sources"
    sourcemap_file_path = root_path / "sources.avm.json"
    app_output_path = root_path / "cool_app"

    assert (sourcemap_file_path).exists()
    assert (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.teal.tok.map").exists()
    assert (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.teal.tok.map").exists()

    result = AVMDebuggerSourceMap.from_dict(json.loads(sourcemap_file_path.read_text()))
    for item in result.txn_group_sources:
        item.location = "dummy"

    check_output_stability(json.dumps(result.to_dict()))

    # check for updates in case of multiple runs
    persist_sourcemaps(sources=sources, project_root=cwd, client=algorand.client.algod)
    result = AVMDebuggerSourceMap.from_dict(json.loads(sourcemap_file_path.read_text()))
    for item in result.txn_group_sources:
        assert item.location != "dummy"


def test_build_teal_sourcemaps_without_sources(
    algorand: AlgorandClient, tmp_path_factory: pytest.TempPathFactory
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
    compiled_approval = Program(approval, algorand.client.algod)
    compiled_clear = Program(clear, algorand.client.algod)
    sources = [
        PersistSourceMapInput(compiled_teal=compiled_approval, app_name="cool_app", file_name="approval.teal"),
        PersistSourceMapInput(compiled_teal=compiled_clear, app_name="cool_app", file_name="clear"),
    ]

    persist_sourcemaps(sources=sources, project_root=cwd, client=algorand.client.algod, with_sources=False)

    root_path = cwd / ".algokit" / "sources"
    sourcemap_file_path = root_path / "sources.avm.json"
    app_output_path = root_path / "cool_app"

    assert (sourcemap_file_path).exists()
    assert not (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.teal.tok.map").exists()
    assert json.loads((app_output_path / "approval.teal.tok.map").read_text())["sources"] == []
    assert not (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.teal.tok.map").exists()
    assert json.loads((app_output_path / "clear.teal.tok.map").read_text())["sources"] == []

    result = AVMDebuggerSourceMap.from_dict(json.loads(sourcemap_file_path.read_text()))
    for item in result.txn_group_sources:
        item.location = "dummy"
    check_output_stability(json.dumps(result.to_dict()))


def test_simulate_and_persist_response_via_app_call(
    tmp_path_factory: pytest.TempPathFactory,
    client_fixture: AppClient,
    mock_config: Mock,
) -> None:
    mock_config.debug = True
    mock_config.trace_all = True
    mock_config.trace_buffer_size_mb = 256
    cwd = tmp_path_factory.mktemp("cwd")
    mock_config.project_root = cwd

    client_fixture.send.call(AppClientMethodCallWithSendParams(method="hello", args=["test"]))

    output_path = cwd / "debug_traces"

    content = list(output_path.iterdir())
    assert len(list(output_path.iterdir())) == 1
    trace_file_content = json.loads(content[0].read_text())
    simulated_txn = trace_file_content["txn-groups"][0]["txn-results"][0]["txn-result"]["txn"]["txn"]
    assert simulated_txn["type"] == "appl"
    assert simulated_txn["apid"] == client_fixture.app_id


def test_simulate_and_persist_response(
    tmp_path_factory: pytest.TempPathFactory, algorand: AlgorandClient, mock_config: Mock, funded_account: Account
) -> None:
    mock_config.debug = True
    mock_config.trace_all = True
    cwd = tmp_path_factory.mktemp("cwd")
    mock_config.project_root = cwd
    algod = algorand.client.algod

    payment = PaymentTxn(
        sender=funded_account.address,
        receiver=funded_account.address,
        amt=1_000_000,
        note=b"Payment",
        sp=algod.suggested_params(),
    )
    txn_with_signer = TransactionWithSigner(payment, AccountTransactionSigner(funded_account.private_key))
    atc = AtomicTransactionComposer()
    atc.add_transaction(txn_with_signer)

    simulate_and_persist_response(atc, cwd, algod)

    output_path = cwd / "debug_traces"
    content = list(output_path.iterdir())
    assert len(list(output_path.iterdir())) == 1
    trace_file_content = json.loads(content[0].read_text())
    simulated_txn = trace_file_content["txn-groups"][0]["txn-results"][0]["txn-result"]["txn"]["txn"]
    assert simulated_txn["type"] == "pay"

    trace_file_path = content[0]
    while trace_file_path.exists():
        tmp_atc = atc.clone()
        simulate_and_persist_response(tmp_atc, cwd, algod, buffer_size_mb=0.003)
