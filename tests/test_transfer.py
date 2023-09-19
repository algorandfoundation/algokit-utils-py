from typing import TYPE_CHECKING

import algosdk
import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    TransferAssetParameters,
    TransferParameters,
    create_kmd_wallet_account,
    ensure_funded,
    get_dispenser_account,
    transfer,
    transfer_asset,
)
from algosdk.util import algos_to_microalgos

from tests.conftest import assure_funds_and_opt_in, check_output_stability, generate_test_asset, get_unique_name

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
    assure_funds_and_opt_in(algod_client=algod_client, account=to_account, asset_id=dummy_asset_id)

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
    assure_funds_and_opt_in(algod_client=algod_client, account=to_account, asset_id=dummy_asset_id)

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
    assure_funds_and_opt_in(algod_client=algod_client, account=to_account, asset_id=dummy_asset_id)
    assure_funds_and_opt_in(algod_client=algod_client, account=clawback_account, asset_id=dummy_asset_id)

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

    clawback_account_info = algod_client.account_asset_info(to_account.address, dummy_asset_id)
    assert isinstance(clawback_account_info, dict)
    assert clawback_account_info["asset-holding"]["amount"] == 5  # noqa: PLR2004

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

    clawback_account_info = algod_client.account_asset_info(to_account.address, dummy_asset_id)
    assert isinstance(clawback_account_info, dict)
    assert clawback_account_info["asset-holding"]["amount"] == 0

    funded_account_info = algod_client.account_asset_info(funded_account.address, dummy_asset_id)
    assert isinstance(funded_account_info, dict)
    assert funded_account_info["asset-holding"]["amount"] == 95  # noqa: PLR2004


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

    assert response.sender == dispenser.address
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
