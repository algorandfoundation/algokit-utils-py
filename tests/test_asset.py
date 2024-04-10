import re
from typing import TYPE_CHECKING

import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    TransferAssetParameters,
    create_kmd_wallet_account,
    ensure_funded,
    transfer_asset,
)
from algokit_utils.asset import opt_in, opt_out

if TYPE_CHECKING:
    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient

from tests.conftest import assure_funds, generate_test_asset, get_unique_name


@pytest.fixture()
def to_account(kmd_client: "KMDClient") -> Account:
    return create_kmd_wallet_account(kmd_client, get_unique_name())


def test_opt_in_assets_succeed(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 1)
    account_info = algod_client.account_info(to_account.address)
    assert isinstance(account_info, dict)
    assert account_info["total-assets-opted-in"] == 0

    assure_funds(algod_client=algod_client, account=to_account)
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
    account_info_after_opt_in = algod_client.account_info(to_account.address)

    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == 1


def test_opt_in_assets_to_account_second_attempt_failed(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 1)
    account_info = algod_client.account_info(to_account.address)
    assert isinstance(account_info, dict)
    assert account_info["total-assets-opted-in"] == 0

    assure_funds(algod_client=algod_client, account=to_account)
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
    account_info_after_opt_in = algod_client.account_info(to_account.address)

    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == 1

    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Assets {[dummy_asset_id]} cannot be opted in. Ensure that they are valid and "
            "that the account has not previously opted into them."
        ),
    ):
        opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])


def test_opt_in_two_batches_of_assets_succeed(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    account_info = algod_client.account_info(to_account.address)
    assert isinstance(account_info, dict)
    assert account_info["total-assets-opted-in"] == 0
    dummy_asset_ids = []
    for _ in range(20):
        dummy_asset_id = generate_test_asset(algod_client, funded_account, 1)
        dummy_asset_ids.append(dummy_asset_id)

    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=to_account,
            min_spending_balance_micro_algos=3000000,
            min_funding_increment_micro_algos=1,
        ),
    )
    opt_in(algod_client=algod_client, account=to_account, asset_ids=dummy_asset_ids)
    account_info_after_opt_in = algod_client.account_info(to_account.address)

    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == len(dummy_asset_ids)


def test_opt_out_asset_succeed(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    account_info = algod_client.account_info(to_account.address)
    assert isinstance(account_info, dict)
    assert account_info["total-assets-opted-in"] == 0

    assure_funds(algod_client=algod_client, account=to_account)
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
    account_info_after_opt_in = algod_client.account_info(to_account.address)

    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == 1

    opt_out(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])


def test_opt_out_two_batches_of_assets_succeed(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_ids = []
    for _ in range(20):
        dummy_asset_id = generate_test_asset(algod_client, funded_account, 1)
        dummy_asset_ids.append(dummy_asset_id)

    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=to_account,
            min_spending_balance_micro_algos=3000000,
            min_funding_increment_micro_algos=1,
        ),
    )
    opt_in(algod_client=algod_client, account=to_account, asset_ids=dummy_asset_ids)
    account_info_after_opt_in = algod_client.account_info(to_account.address)
    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == len(dummy_asset_ids)

    opt_out(algod_client=algod_client, account=to_account, asset_ids=dummy_asset_ids)
    account_info_after_opt_out = algod_client.account_info(to_account.address)
    assert isinstance(account_info_after_opt_out, dict)
    assert account_info_after_opt_out["total-assets-opted-in"] == 0


def test_opt_out_of_not_opted_in_asset_failed(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 1)
    account_info = algod_client.account_info(to_account.address)
    assert isinstance(account_info, dict)
    assert account_info["total-assets-opted-in"] == 0

    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Assets {[dummy_asset_id]} cannot be opted out. Ensure that their amount is zero "
            "and that the account has previously opted into them."
        ),
    ):
        opt_out(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])


def test_opt_out_of_non_zero_balance_asset_failed(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    dummy_asset_id = generate_test_asset(algod_client, funded_account, 100)
    assure_funds(algod_client=algod_client, account=to_account)
    opt_in(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
    account_info_after_opt_in = algod_client.account_info(to_account.address)
    assert isinstance(account_info_after_opt_in, dict)
    assert account_info_after_opt_in["total-assets-opted-in"] == 1

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
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Assets {[dummy_asset_id]} cannot be opted out. Ensure that their amount is zero "
            "and that the account has previously opted into them."
        ),
    ):
        opt_out(algod_client=algod_client, account=to_account, asset_ids=[dummy_asset_id])
