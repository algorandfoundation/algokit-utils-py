from algokit_utils import get_account
from algosdk.v2client.algod import AlgodClient

from tests.conftest import get_unique_name


def test_account_can_be_called_twice(algod_client: AlgodClient) -> None:
    account_name = get_unique_name()
    account1 = get_account(algod_client, account_name)
    account2 = get_account(algod_client, account_name)

    assert account1 == account2
