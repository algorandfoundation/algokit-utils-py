from typing import TYPE_CHECKING

import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    TransferParameters,
    create_kmd_wallet_account,
    ensure_funded,
    transfer,
)
from algosdk.util import algos_to_microalgos

from tests.conftest import check_output_stability, get_unique_name

if TYPE_CHECKING:
    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient


MINIMUM_BALANCE = 100_000  # see https://developer.algorand.org/docs/get-details/accounts/#minimum-balance


@pytest.fixture()
def to_account(kmd_client: "KMDClient") -> Account:
    return create_kmd_wallet_account(kmd_client, get_unique_name())


def test_transfer(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
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


def test_transfer_max_fee_fails(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
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


def test_transfer_fee(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
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
