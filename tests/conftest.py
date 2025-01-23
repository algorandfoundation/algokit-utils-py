import inspect
import math
import random
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    EnsureBalanceParameters,
    ensure_funded,
    replace_template_variables,
)
from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.app_manager import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME
from algokit_utils.transactions.transaction_composer import AssetCreateParams

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


@pytest.fixture(autouse=True, scope="session")
def _environment_fixture() -> None:
    env_path = Path(__file__).parent / ".." / "example.env"
    load_dotenv(env_path)


def check_output_stability(logs: str, *, test_name: str | None = None) -> None:
    """Test that the contract output hasn't changed for an Application, using git diff"""
    caller_frame = inspect.stack()[1]
    caller_path = Path(caller_frame.filename).resolve()
    caller_dir = caller_path.parent
    test_name = test_name or caller_frame.function
    caller_stem = Path(caller_frame.filename).stem
    output_dir = caller_dir / "_snapshots" / f"{caller_stem}.approvals"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{test_name}.approved.txt"
    output_file_str = str(output_file)
    output_file_did_exist = output_file.exists()
    output_file.write_text(logs, encoding="utf-8")

    git_diff = subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            "--no-ext-diff",
            "--no-color",
            output_file_str,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    # first fail if there are any changes to already committed files, you must manually add them in that case
    assert git_diff.returncode == 0, git_diff.stdout

    # if first time running, fail in case of accidental change to output directory
    if not output_file_did_exist:
        pytest.fail(
            f"New output folder created at {output_file_str} from test {test_name} - "
            "if this was intentional, please commit the files to the git repo"
        )


def read_spec(
    file_name: str,
    *,
    updatable: bool | None = None,
    deletable: bool | None = None,
    template_values: dict | None = None,
) -> ApplicationSpecification:
    path = Path(__file__).parent / file_name
    spec = ApplicationSpecification.from_json(Path(path).read_text(encoding="utf-8"))

    template_variables = template_values or {}
    if updatable is not None:
        template_variables["UPDATABLE"] = int(updatable)

    if deletable is not None:
        template_variables["DELETABLE"] = int(deletable)

    spec.approval_program = (
        replace_template_variables(spec.approval_program, template_variables)
        .replace(f"// {UPDATABLE_TEMPLATE_NAME}", "// updatable")
        .replace(f"// {DELETABLE_TEMPLATE_NAME}", "// deletable")
    )
    return spec


def get_specs(
    updatable: bool | None = None,
    deletable: bool | None = None,
) -> tuple[ApplicationSpecification, ApplicationSpecification, ApplicationSpecification]:
    return (
        read_spec("app_v1.json", updatable=updatable, deletable=deletable),
        read_spec("app_v2.json", updatable=updatable, deletable=deletable),
        read_spec("app_v3.json", updatable=updatable, deletable=deletable),
    )


def get_unique_name() -> str:
    name = str(uuid4()).replace("-", "")
    assert name.isalnum()
    return name


def is_opted_in(client_fixture: ApplicationClient) -> bool:
    _, sender = client_fixture.resolve_signer_sender()
    account_info = client_fixture.algod_client.account_info(sender)
    assert isinstance(account_info, dict)
    apps_local_state = account_info["apps-local-state"]
    return any(x for x in apps_local_state if x["id"] == client_fixture.app_id)


def generate_test_asset(algorand: AlgorandClient, sender: Account, total: int | None) -> int:
    if total is None:
        total = math.floor(random.random() * 100) + 20

    decimals = 0
    asset_name = f"ASA ${math.floor(random.random() * 100) + 1}_${math.floor(random.random() * 100) + 1}_${total}"

    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=sender.address,
            total=total,
            decimals=decimals,
            default_frozen=False,
            unit_name="CFG",
            asset_name=asset_name,
            url="https://example.com",
            manager=sender.address,
            reserve=sender.address,
            freeze=sender.address,
            clawback=sender.address,
        )
    )

    return int(create_result.confirmation["asset-index"])  # type: ignore[call-overload]


def assure_funds(algod_client: "AlgodClient", account: Account) -> None:
    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=account,
            min_spending_balance_micro_algos=300000,
            min_funding_increment_micro_algos=1,
        ),
    )
