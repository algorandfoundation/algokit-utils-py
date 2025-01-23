import json
import os
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from algosdk.abi.method import Method
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import PaymentTxn

from algokit_utils._debugging import (
    PersistSourceMapInput,
    cleanup_old_trace_files,
    persist_sourcemaps,
    simulate_and_persist_response,
)
from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications import AppFactoryCreateMethodCallParams
from algokit_utils.applications.app_client import (
    AppClient,
    AppClientMethodCallWithSendParams,
)
from algokit_utils.common import Program
from algokit_utils.models import Account
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AppCallMethodCallParams,
    AssetCreateParams,
    AssetTransferParams,
    PaymentParams,
)


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
        min_spending_balance=AlgoAmount.from_algo(100),
        min_funding_increment=AlgoAmount.from_algo(100),
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

    assert not (sourcemap_file_path).exists()
    assert (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.teal.map").exists()
    assert (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.teal.map").exists()


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

    assert not (sourcemap_file_path).exists()
    assert not (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.teal.map").exists()
    assert json.loads((app_output_path / "approval.teal.map").read_text())["sources"] == []
    assert not (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.teal.map").exists()
    assert json.loads((app_output_path / "clear.teal.map").read_text())["sources"] == []


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


@pytest.mark.parametrize(
    ("transactions", "expected_filename_part"),
    [
        # Single transaction types
        ({"pay": 1}, "1pay"),
        ({"axfer": 1}, "1axfer"),
        ({"appl": 1}, "1appl"),
        # Multiple of same type
        ({"pay": 3}, "3pay"),
        ({"axfer": 2}, "2axfer"),
        ({"appl": 4}, "4appl"),
        # Mixed combinations
        ({"pay": 2, "axfer": 1, "appl": 3}, "2pay_1axfer_3appl"),
        ({"pay": 1, "axfer": 1, "appl": 1}, "1pay_1axfer_1appl"),
    ],
)
def test_simulate_response_filename_generation(
    transactions: dict[str, int],
    expected_filename_part: str,
    tmp_path_factory: pytest.TempPathFactory,
    client_fixture: AppClient,
    funded_account: Account,
    monkeypatch: pytest.MonkeyPatch,
    mock_config: Mock,
) -> None:
    asset_id = 1
    if "axfer" in transactions:
        asset_id = client_fixture.algorand.send.asset_create(
            AssetCreateParams(
                sender=funded_account.address,
                total=100_000_000,
                decimals=0,
                unit_name="TEST",
                asset_name="Test Asset",
            )
        ).asset_id

    cwd = tmp_path_factory.mktemp("cwd")
    mock_config.debug = True
    mock_config.trace_all = True
    mock_config.trace_buffer_size_mb = 256
    mock_config.project_root = cwd
    atc = client_fixture.algorand.new_group()

    # Add payment transactions
    for i in range(transactions.get("pay", 0)):
        atc.add_payment(
            PaymentParams(
                sender=funded_account.address,
                receiver=client_fixture.app_address,
                amount=AlgoAmount.from_micro_algos(1_000_000 * (i + 1)),
                note=f"Payment{i+1}".encode(),
            )
        )

    # Add asset transfer transactions
    for i in range(transactions.get("axfer", 0)):
        atc.add_asset_transfer(
            AssetTransferParams(
                sender=funded_account.address,
                receiver=funded_account.address,
                amount=1_000 * (i + 1),
                asset_id=asset_id,
            )
        )

    # Add app calls
    for i in range(transactions.get("appl", 0)):
        atc.add_app_call_method_call(
            AppCallMethodCallParams(
                method=Method.from_signature("hello(string)string"),
                args=[f"test{i+1}"],
                sender=funded_account.address,
                app_id=client_fixture.app_id,
            )
        )

    # Mock datetime
    mock_datetime = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    class MockDateTime:
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:  # noqa: ARG003
            return mock_datetime

    monkeypatch.setattr("algokit_utils._debugging.datetime", MockDateTime)

    response = atc.simulate()
    assert response.simulate_response
    last_round = response.simulate_response["last-round"]
    expected_filename = f"20230101_120000_lr{last_round}_{expected_filename_part}.trace.avm.json"

    # Verify file exists with expected name
    output_path = cwd / "debug_traces"
    files = list(output_path.iterdir())
    assert len(files) == 1
    assert files[0].name == expected_filename

    # Verify transaction count
    trace_file_content = json.loads(files[0].read_text())
    txn_results = trace_file_content["txn-groups"][0]["txn-results"]
    expected_total_txns = sum(transactions.values())
    assert len(txn_results) == expected_total_txns


@dataclass
class TestFile:
    name: str
    content: bytes
    mtime: datetime


def test_removes_oldest_files_when_buffer_size_exceeded(
    tmp_path_factory: pytest.TempPathFactory, mock_config: Mock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    trace_dir = cwd / "debug_traces"
    trace_dir.mkdir(exist_ok=True)
    mock_config.debug = True
    mock_config.trace_all = True
    mock_config.trace_buffer_size_mb = 256
    mock_config.project_root = cwd

    # Create test files with different timestamps and sizes
    test_files: list[TestFile] = [
        TestFile(name="old.json", content=b"a" * (1024 * 1024), mtime=datetime(2023, 1, 1, tzinfo=timezone.utc)),
        TestFile(name="newer.json", content=b"b" * (1024 * 1024), mtime=datetime(2023, 1, 2, tzinfo=timezone.utc)),
        TestFile(name="newest.json", content=b"c" * (1024 * 1024), mtime=datetime(2023, 1, 3, tzinfo=timezone.utc)),
    ]

    # Create files with specific timestamps
    for file in test_files:
        file_path = trace_dir / file.name
        file_path.write_bytes(file.content)
        os.utime(file_path, (file.mtime.timestamp(), file.mtime.timestamp()))

    # Set buffer size to 2MB (should remove oldest file)
    cleanup_old_trace_files(trace_dir, buffer_size_mb=2.0)

    # Check remaining files
    remaining_files = list(trace_dir.iterdir())
    remaining_names = [f.name for f in remaining_files]

    assert len(remaining_files) == 2
    assert "newer.json" in remaining_names
    assert "newest.json" in remaining_names
    assert "old.json" not in remaining_names


def test_does_nothing_when_total_size_within_buffer_limit(
    tmp_path_factory: pytest.TempPathFactory, mock_config: Mock
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    mock_config.debug = True
    mock_config.trace_all = True
    mock_config.trace_buffer_size_mb = 256
    mock_config.project_root = cwd

    # Create test directory
    trace_dir = cwd / "debug_traces"
    trace_dir.mkdir()

    # Create two 512KB files (total 1MB)
    content = b"a" * (512 * 1024)  # 512KB
    (trace_dir / "file1.json").write_bytes(content)
    (trace_dir / "file2.json").write_bytes(content)

    # Set buffer size to 2MB (files total 1MB, should not remove anything)
    cleanup_old_trace_files(trace_dir, buffer_size_mb=2.0)

    remaining_files = list(trace_dir.iterdir())
    assert len(remaining_files) == 2
