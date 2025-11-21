import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from algokit_algosdk.abi.method import Method
from algokit_utils._debugging import (
    PersistSourceMapInput,
    cleanup_old_trace_files,
    persist_sourcemaps,
    simulate_and_persist_response,
)
from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications import AppFactoryCreateMethodCallParams
from algokit_utils.applications.app_client import AppClient
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.models import SigningAccount
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
def funded_account(algorand: AlgorandClient) -> SigningAccount:
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
def client_fixture(algorand: AlgorandClient, funded_account: SigningAccount) -> AppClient:
    app_spec = (Path(__file__).parent / "artifacts" / "legacy_app_client_test" / "app_client_test.json").read_text()
    app_factory = algorand.client.get_app_factory(
        app_spec=app_spec, default_sender=funded_account.address, default_signer=funded_account.signer
    )
    app_client, _ = app_factory.send.create(
        AppFactoryCreateMethodCallParams(method="create"),
        compilation_params={
            "deletable": True,
            "updatable": True,
            "deploy_time_params": {"VERSION": 1},
        },
    )
    return app_client


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
    app_output_path = root_path / "cool_app"

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
    app_manager = AppManager(algorand.client.algod)
    compiled_approval = app_manager.compile_teal(AppManager.strip_teal_comments(approval))
    compiled_clear = app_manager.compile_teal(AppManager.strip_teal_comments(clear))
    sources = [
        PersistSourceMapInput(compiled_teal=compiled_approval, app_name="cool_app", file_name="approval.teal"),
        PersistSourceMapInput(compiled_teal=compiled_clear, app_name="cool_app", file_name="clear"),
    ]

    persist_sourcemaps(sources=sources, project_root=cwd, client=algorand.client.algod, with_sources=False)

    root_path = cwd / ".algokit" / "sources"
    app_output_path = root_path / "cool_app"

    assert not (app_output_path / "approval.teal").exists()
    assert (app_output_path / "approval.teal.map").exists()
    assert json.loads((app_output_path / "approval.teal.map").read_text())["sources"] == []
    assert not (app_output_path / "clear.teal").exists()
    assert (app_output_path / "clear.teal.map").exists()
    assert json.loads((app_output_path / "clear.teal.map").read_text())["sources"] == []


@dataclass
class TestFile:
    __test__ = False

    name: str
    content: bytes
    mtime: datetime


def test_removes_oldest_files_when_buffer_size_exceeded(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    trace_dir = cwd / "debug_traces"
    trace_dir.mkdir(exist_ok=True)

    test_files: list[TestFile] = [
        TestFile(name="old.json", content=b"a" * (1024 * 1024), mtime=datetime(2023, 1, 1, tzinfo=timezone.utc)),
        TestFile(name="newer.json", content=b"b" * (1024 * 1024), mtime=datetime(2023, 1, 2, tzinfo=timezone.utc)),
        TestFile(name="newest.json", content=b"c" * (1024 * 1024), mtime=datetime(2023, 1, 3, tzinfo=timezone.utc)),
    ]

    for file in test_files:
        file_path = trace_dir / file.name
        file_path.write_bytes(file.content)
        os.utime(file_path, (file.mtime.timestamp(), file.mtime.timestamp()))

    cleanup_old_trace_files(trace_dir, buffer_size_mb=2.0)

    remaining_files = list(trace_dir.iterdir())
    remaining_names = {f.name for f in remaining_files}

    assert "old.json" not in remaining_names
    assert {"newer.json", "newest.json"} == remaining_names


def test_does_nothing_when_total_size_within_buffer_limit(tmp_path_factory: pytest.TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    trace_dir = cwd / "debug_traces"
    trace_dir.mkdir(exist_ok=True)

    file_path = trace_dir / "trace.json"
    file_path.write_bytes(b"a" * 1024)

    cleanup_old_trace_files(trace_dir, buffer_size_mb=2.0)

    assert (trace_dir / "trace.json").exists()


def test_simulate_and_persist_response(tmp_path_factory: pytest.TempPathFactory, algorand: AlgorandClient) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    composer = algorand.new_group()
    composer.add_payment(
        PaymentParams(
            sender=algorand.account.localnet_dispenser().address,
            receiver=algorand.account.localnet_dispenser().address,
            amount=AlgoAmount.from_micro_algo(1_000_000),
        )
    )

    persisted = simulate_and_persist_response(composer, cwd, algorand.client.algod)

    assert persisted.exists()
    trace = json.loads(persisted.read_text())
    txn = trace["txn-groups"][0]["txn-results"][0]["txn-result"]["txn"]["txn"]
    assert txn["type"] == "pay"


def test_simulate_and_persist_response_via_app_call(
    tmp_path_factory: pytest.TempPathFactory,
    client_fixture: AppClient,
    funded_account: SigningAccount,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    composer = client_fixture.algorand.new_group()
    composer.add_app_call_method_call(
        AppCallMethodCallParams(
            method=Method.from_signature("hello(string)string"),
            args=["test"],
            sender=funded_account.address,
            app_id=client_fixture.app_id,
        )
    )

    persisted = simulate_and_persist_response(composer, cwd, client_fixture.algorand.client.algod)

    assert persisted.exists()
    trace = json.loads(persisted.read_text())
    txn = trace["txn-groups"][0]["txn-results"][0]["txn-result"]["txn"]["txn"]
    assert txn["type"] == "appl"
    assert txn["apid"] == client_fixture.app_id


@pytest.mark.parametrize(
    ("transactions", "expected_filename_part"),
    [
        ({"pay": 1}, "1pay"),
        ({"axfer": 1}, "1axfer"),
        ({"appl": 1}, "1appl"),
        ({"pay": 3}, "3pay"),
        ({"axfer": 2}, "2axfer"),
        ({"appl": 4}, "4appl"),
        ({"pay": 2, "axfer": 1, "appl": 3}, "2pay_1axfer_3appl"),
        ({"pay": 1, "axfer": 1, "appl": 1}, "1pay_1axfer_1appl"),
    ],
)
def test_simulate_response_filename_generation(
    transactions: dict[str, int],
    expected_filename_part: str,
    tmp_path_factory: pytest.TempPathFactory,
    client_fixture: AppClient,
    funded_account: SigningAccount,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    composer = client_fixture.algorand.new_group()

    if transactions.get("axfer"):
        asset_id = client_fixture.algorand.send.asset_create(
            AssetCreateParams(
                sender=funded_account.address,
                total=100_000_000,
                decimals=0,
                unit_name="TEST",
                asset_name="Test Asset",
            )
        ).asset_id
    else:
        asset_id = 1

    for i in range(transactions.get("pay", 0)):
        composer.add_payment(
            PaymentParams(
                sender=funded_account.address,
                receiver=client_fixture.app_address,
                amount=AlgoAmount.from_micro_algo(1_000_000 * (i + 1)),
                note=f"Payment{i + 1}".encode(),
            )
        )
    for i in range(transactions.get("axfer", 0)):
        composer.add_asset_transfer(
            AssetTransferParams(
                sender=funded_account.address,
                receiver=funded_account.address,
                amount=1_000 * (i + 1),
                asset_id=asset_id,
            )
        )
    for i in range(transactions.get("appl", 0)):
        composer.add_app_call_method_call(
            AppCallMethodCallParams(
                method=Method.from_signature("hello(string)string"),
                args=[f"test{i + 1}"],
                sender=funded_account.address,
                app_id=client_fixture.app_id,
            )
        )

    mock_datetime = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    class MockDateTime:
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:  # noqa: ARG003
            return mock_datetime

    import algokit_utils._debugging as debug_mod

    monkeypatch.setattr(debug_mod, "datetime", MockDateTime)
    persisted = simulate_and_persist_response(composer, cwd, client_fixture.algorand.client.algod)

    assert persisted.name.startswith("20230101_120000_lr")
    assert expected_filename_part in persisted.name

    trace = json.loads(persisted.read_text())
    txn_results = trace["txn-groups"][0]["txn-results"]
    assert len(txn_results) == sum(transactions.values())
