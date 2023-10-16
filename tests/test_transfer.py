from typing import TYPE_CHECKING

import algosdk
import httpx
import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    EnsureFundedResponse,
    TestNetDispenserApiClient,
    TransferAssetParameters,
    TransferParameters,
    create_kmd_wallet_account,
    ensure_funded,
    get_dispenser_account,
    transfer,
    transfer_asset, opt_in,
)
from algokit_utils.dispenser_api import DispenserApiConfig
from algokit_utils.network_clients import get_algod_client, get_algonode_config
from algosdk.util import algos_to_microalgos
from pytest_httpx import HTTPXMock

from tests.conftest import check_output_stability, generate_test_asset, get_unique_name, \
    assure_funds
from tests.test_network_clients import DEFAULT_TOKEN

if TYPE_CHECKING:
    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient


MINIMUM_BALANCE = 100_000  # see https://developer.algorand.org/docs/get-details/accounts/#minimum-balance


@pytest.fixture()
def to_account(kmd_client: "KMDClient") -> Account:
    return create_kmd_wallet_account(kmd_client, get_unique_name())


@pytest.fixture()
def clawback_account(kmd_client: "KMDClient") -> Account:
    return create_kmd_wallet_account(kmd_client, get_unique_name())


def test_transfer_algo(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    requested_amount = 100_000
    transfer(
        algod_client,
        TransferParameters(
            from_account=funded_account,
            to_address=to_account.address,
            micro_algos=requested_amount,
        ),
    )

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == requested_amount


def test_transfer_algo_max_fee_fails(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    requested_amount = 100_000
    max_fee = 123

    with pytest.raises(Exception, match="Cancelled transaction due to high network congestion fees") as ex:
        transfer(
            algod_client,
            TransferParameters(
                from_account=funded_account,
                to_address=to_account.address,
                micro_algos=requested_amount,
                max_fee_micro_algos=max_fee,
            ),
        )

    check_output_stability(str(ex.value))


def test_transfer_algo_fee(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    requested_amount = 100_000
    fee = 1234
    txn = transfer(
        algod_client,
        TransferParameters(
            from_account=funded_account,
            to_address=to_account.address,
            micro_algos=requested_amount,
            fee_micro_algos=fee,
        ),
    )

    assert txn.fee == fee


def test_transfer_asa_receiver_not_optin(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    with pytest.raises(algosdk.error.AlgodHTTPError, match="receiver error: must optin"):
        transfer_asset(
            algod_client,
            TransferAssetParameters(
                from_account=funded_account,
                to_address=to_account.address,
                asset_id=dummy_asset_id,
                amount=5,
                note=f"Transfer 5 assets wit id ${dummy_asset_id}",
            ),
        )


def test_transfer_asa_asset_doesnt_exist(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    assure_funds(algod_client=algod_client, account=to_account)
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])

    with pytest.raises(algosdk.error.AlgodHTTPError, match="asset 1 missing from"):
        transfer_asset(
            algod_client,
            TransferAssetParameters(
                from_account=funded_account,
                to_address=to_account.address,
                asset_id=1,
                amount=5,
                note=f"Transfer 5 assets wit id ${dummy_asset_id}",
            ),
        )


def test_transfer_asa_asset_is_transfered(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    assure_funds(algod_client=algod_client, account=to_account)
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
    transfer_asset(
        algod_client,
        TransferAssetParameters(
            from_account=funded_account,
            to_address=to_account.address,
            asset_id=dummy_asset_id,
            amount=5,
            note=f"Transfer 5 assets wit id ${dummy_asset_id}",
        ),
    )

    to_account_info = algod_client.account_asset_info(to_account.address, dummy_asset_id)
    assert isinstance(to_account_info, dict)
    assert to_account_info["asset-holding"]["amount"] == 5  # noqa: PLR2004

    funded_account_info = algod_client.account_asset_info(funded_account.address, dummy_asset_id)
    assert isinstance(funded_account_info, dict)
    assert funded_account_info["asset-holding"]["amount"] == 95  # noqa: PLR2004


def test_transfer_asa_asset_is_transfered_from_revocation_target(
    algod_client: "AlgodClient", to_account: Account, clawback_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    assure_funds(algod_client=algod_client, account=to_account)
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])

    assure_funds(algod_client=algod_client, account=clawback_account)
    opt_in(algod_client=algod_client, account=clawback_account, asset_ids=[dummy_asset_id])

    transfer_asset(
        algod_client,
        TransferAssetParameters(
            from_account=funded_account,
            to_address=clawback_account.address,
            asset_id=dummy_asset_id,
            amount=5,
            note=f"Transfer 5 assets wit id ${dummy_asset_id}",
        ),
    )

    clawback_account_info = algod_client.account_asset_info(clawback_account.address, dummy_asset_id)
    assert isinstance(clawback_account_info, dict)
    assert clawback_account_info["asset-holding"]["amount"] == 5  # noqa: PLR2004

    transfer_asset(
        algod_client,
        TransferAssetParameters(
            from_account=funded_account,
            to_address=to_account.address,
            clawback_from=clawback_account.address,
            asset_id=dummy_asset_id,
            amount=5,
            note=f"Transfer 5 assets wit id ${dummy_asset_id}",
        ),
    )

    to_account_info = algod_client.account_asset_info(to_account.address, dummy_asset_id)
    assert isinstance(to_account_info, dict)
    assert to_account_info["asset-holding"]["amount"] == 5  # noqa: PLR2004

    clawback_account_info = algod_client.account_asset_info(clawback_account.address, dummy_asset_id)
    assert isinstance(clawback_account_info, dict)
    assert clawback_account_info["asset-holding"]["amount"] == 0

    funded_account_info = algod_client.account_asset_info(funded_account.address, dummy_asset_id)
    assert isinstance(funded_account_info, dict)
    assert funded_account_info["asset-holding"]["amount"] == 95  # noqa: PLR2004


def test_transfer_asset_max_fee_fails(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    with pytest.raises(Exception, match="Cancelled transaction due to high network congestion fees") as ex:
        transfer_asset(
            algod_client,
            TransferAssetParameters(
                from_account=funded_account,
                to_address=to_account.address,
                asset_id=dummy_asset_id,
                amount=5,
                note=f"Transfer 5 assets wit id ${dummy_asset_id}",
                max_fee_micro_algos=123,
            ),
        )

    check_output_stability(str(ex.value))


def test_ensure_funded(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    parameters = EnsureBalanceParameters(
        funding_source=funded_account,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == MINIMUM_BALANCE + 1


def test_ensure_funded_uses_dispenser_by_default(algod_client: "AlgodClient", to_account: Account) -> None:
    dispenser = get_dispenser_account(algod_client)
    parameters = EnsureBalanceParameters(
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None
    assert isinstance(response, EnsureFundedResponse)

    txn_info = algod_client.pending_transaction_info(response.transaction_id)
    assert isinstance(txn_info, dict)
    assert txn_info["txn"]["txn"]["snd"] == dispenser.address

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == MINIMUM_BALANCE + 1


def test_ensure_funded_correct_amount(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    parameters = EnsureBalanceParameters(
        funding_source=funded_account,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == MINIMUM_BALANCE + 1


def test_ensure_funded_respects_minimum_funding(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    parameters = EnsureBalanceParameters(
        funding_source=funded_account,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
        min_funding_increment_micro_algos=algos_to_microalgos(1),  # type: ignore[no-untyped-call]
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == algos_to_microalgos(1)  # type: ignore[no-untyped-call]


def test_ensure_funded_testnet_api_success(
    to_account: Account, monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock
) -> None:
    monkeypatch.setenv(
        "ALGOKIT_DISPENSER_ACCESS_TOKEN",
        "dummy",
    )
    httpx_mock.add_response(
        url=f"{DispenserApiConfig.BASE_URL}/fund/0",
        method="POST",
        json={"amount": 1, "txID": "dummy_tx_id"},
    )

    algod_client = get_algod_client(get_algonode_config("testnet", "algod", DEFAULT_TOKEN))

    dispenser_client = TestNetDispenserApiClient()
    parameters = EnsureBalanceParameters(
        funding_source=dispenser_client,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None
    assert response.transaction_id == "dummy_tx_id"
    assert response.amount == 1


def test_ensure_funded_testnet_api_bad_response(
    to_account: Account, monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock
) -> None:
    monkeypatch.setenv(
        "ALGOKIT_DISPENSER_ACCESS_TOKEN",
        "dummy",
    )
    httpx_mock.add_exception(
        httpx.HTTPStatusError(
            "Limit exceeded",
            request=httpx.Request("POST", f"{DispenserApiConfig.BASE_URL}/fund"),
            response=httpx.Response(
                400,
                request=httpx.Request("POST", f"{DispenserApiConfig.BASE_URL}/fund"),
                json={
                    "code": "fund_limit_exceeded",
                    "limit": 10_000_000,
                    "resetsAt": "2023-09-19T10:07:34.024Z",
                },
            ),
        ),
        url=f"{DispenserApiConfig.BASE_URL}/fund/0",
        method="POST",
    )

    algod_client = get_algod_client(get_algonode_config("testnet", "algod", DEFAULT_TOKEN))

    dispenser_client = TestNetDispenserApiClient()
    parameters = EnsureBalanceParameters(
        funding_source=dispenser_client,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )

    with pytest.raises(Exception, match="fund_limit_exceeded"):
        ensure_funded(algod_client, parameters)
