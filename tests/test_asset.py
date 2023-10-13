from typing import TYPE_CHECKING

import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    create_kmd_wallet_account,
    ensure_funded,
)
from algokit_utils.asset import opt_in, opt_out

if TYPE_CHECKING:
    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient

from tests.conftest import generate_test_asset, get_unique_name


@pytest.fixture()
def to_account(kmd_client: "KMDClient") -> Account:
    return create_kmd_wallet_account(kmd_client, get_unique_name())


def test_opt_in(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    account_info = algod_client.account_info(to_account.address)
    assert isinstance(account_info, dict)
    assert account_info["total-assets-opted-in"] == 0

    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=to_account,
            min_spending_balance_micro_algos=300000,
            min_funding_increment_micro_algos=1,
        ),
    )
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
    account_info_after_opt_in = algod_client.account_info(to_account.address)

    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == 1


def test_opt_out(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    account_info = algod_client.account_info(to_account.address)
    assert isinstance(account_info, dict)
    assert account_info["total-assets-opted-in"] == 0

    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=to_account,
            min_spending_balance_micro_algos=300000,
            min_funding_increment_micro_algos=1,
        ),
    )
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
    account_info_after_opt_in = algod_client.account_info(to_account.address)

    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == 1

    opt_out(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
