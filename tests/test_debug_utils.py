import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from algokit_utils._debugging import (
    PersistSourceMapInput,
    cleanup_old_trace_files,
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
from algosdk.transaction import AssetTransferTxn, PaymentTxn

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
def test_simulate_response_filename_generation(  # noqa: PLR0913
    transactions: dict[str, int],
    expected_filename_part: str,
    tmp_path_factory: pytest.TempPathFactory,
    client_fixture: ApplicationClient,
    funded_account: Account,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    sp = client_fixture.algod_client.suggested_params()
    atc = AtomicTransactionComposer()
    signer = AccountTransactionSigner(funded_account.private_key)

    # Add payment transactions
    for i in range(transactions.get("pay", 0)):
        payment = PaymentTxn(
            sender=funded_account.address,
            receiver=client_fixture.app_address,
            amt=1_000_000 * (i + 1),
            note=f"Payment{i+1}".encode(),
            sp=sp,
        )  # type: ignore[no-untyped-call]
        atc.add_transaction(TransactionWithSigner(payment, signer))

    # Add asset transfer transactions
    for i in range(transactions.get("axfer", 0)):
        asset_transfer = AssetTransferTxn(
            sender=funded_account.address,
            receiver=client_fixture.app_address,
            amt=1_000 * (i + 1),
            index=1,  # Using asset ID 1 for test
            sp=sp,
        )  # type: ignore[no-untyped-call]
        atc.add_transaction(TransactionWithSigner(asset_transfer, signer))

    # Add app calls
    for i in range(transactions.get("appl", 0)):
        client_fixture.compose_call(atc, "hello", name=f"test{i+1}")

    # Mock datetime
    mock_datetime = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    class MockDateTime:
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:  # noqa: ARG003
            return mock_datetime

    monkeypatch.setattr("algokit_utils._debugging.datetime", MockDateTime)

    response = simulate_and_persist_response(atc, cwd, client_fixture.algod_client)
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


def test_removes_oldest_files_when_buffer_size_exceeded(tmp_path: Path) -> None:
    # Create test directory
    trace_dir = tmp_path / "debug_traces"
    trace_dir.mkdir()

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

    assert len(remaining_files) == 2  # noqa: PLR2004
    assert "newer.json" in remaining_names
    assert "newest.json" in remaining_names
    assert "old.json" not in remaining_names


def test_does_nothing_when_total_size_within_buffer_limit(tmp_path: Path) -> None:
    # Create test directory
    trace_dir = tmp_path / "debug_traces"
    trace_dir.mkdir()

    # Create two 512KB files (total 1MB)
    content = b"a" * (512 * 1024)  # 512KB
    (trace_dir / "file1.json").write_bytes(content)
    (trace_dir / "file2.json").write_bytes(content)

    # Set buffer size to 2MB (files total 1MB, should not remove anything)
    cleanup_old_trace_files(trace_dir, buffer_size_mb=2.0)

    remaining_files = list(trace_dir.iterdir())
    assert len(remaining_files) == 2  # noqa: PLR2004
