from typing import TYPE_CHECKING

import pytest
from algokit_utils import Account, TransferParameters, create_kmd_wallet_account, transfer

from tests.conftest import check_output_stability, get_unique_name

if TYPE_CHECKING:
    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient


@pytest.fixture(scope="module")
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
