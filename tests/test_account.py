from typing import TYPE_CHECKING

from algokit_utils import get_account

from tests.conftest import get_unique_name

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


def test_account_can_be_called_twice(algod_client: "AlgodClient") -> None:
    account_name = get_unique_name()
    account1 = get_account(algod_client, account_name)
    account2 = get_account(algod_client, account_name)

    assert account1 == account2
