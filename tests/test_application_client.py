from dataclasses import dataclass
from pathlib import Path

from algokit_utils import ApplicationClient
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient


class Generated:
    def __init__(self, client: ApplicationClient):
        self._client = client

    def increment(self) -> int:
        return self._client.call("increment").return_value

    def decrement(self) -> int:
        return self._client.call("decrement").return_value


def test_counter():
    client = _get_sandbox_client()

    accounts = _get_accounts()
    account = accounts.pop()

    # Create an Application client containing both an algod client and my app
    app_client = ApplicationClient(client, Path("counter_application.json"), signer=account.signer)
    api = Generated(app_client)

    # Create the application on chain, set the app id for the app client
    create_result = app_client.create()
    print(
        f"Created App with id: {create_result.app_id}, address: {create_result.app_address} in "
        f"transaction: {create_result.transaction_id}"
    )

    api.increment()
    api.increment()
    api.increment()
    result = api.increment()
    print(f"Current counter value: {result}")

    result = api.decrement()
    print(f"Current counter value: {result}")


DEFAULT_KMD_ADDRESS = "http://localhost:4002"
DEFAULT_KMD_TOKEN = "a" * 64
DEFAULT_KMD_WALLET_NAME = "unencrypted-default-wallet"
DEFAULT_KMD_WALLET_PASSWORD = ""


@dataclass
class SandboxAccount:
    """SandboxAccount is a simple dataclass to hold a sandbox account details"""

    #: The address of a sandbox account
    address: str
    #: The base64 encoded private key of the account
    private_key: str
    #: An AccountTransactionSigner that can be used as a TransactionSigner
    signer: AccountTransactionSigner


def _get_sandbox_client() -> AlgodClient:
    return AlgodClient("a" * 64, "http://localhost:4001")


def _get_accounts(
    kmd_address: str = DEFAULT_KMD_ADDRESS,
    kmd_token: str = DEFAULT_KMD_TOKEN,
    wallet_name: str = DEFAULT_KMD_WALLET_NAME,
    wallet_password: str = DEFAULT_KMD_WALLET_PASSWORD,
) -> list[SandboxAccount]:
    """gets all the accounts in the sandbox kmd, defaults
    to the `unencrypted-default-wallet` created on private networks automatically"""

    kmd = KMDClient(kmd_token, kmd_address)
    wallets = kmd.list_wallets()

    wallet_id = None
    for wallet in wallets:
        if wallet["name"] == wallet_name:
            wallet_id = wallet["id"]
            break

    if wallet_id is None:
        raise Exception(f"Wallet not found: {wallet_name}")

    wallet_handle = kmd.init_wallet_handle(wallet_id, wallet_password)

    try:
        addresses = kmd.list_keys(wallet_handle)
        private_keys = [kmd.export_key(wallet_handle, wallet_password, addr) for addr in addresses]
        kmd_accounts = [
            SandboxAccount(addresses[i], private_keys[i], AccountTransactionSigner(private_keys[i]))
            for i in range(len(private_keys))
        ]
    finally:
        kmd.release_wallet_handle(wallet_handle)

    return kmd_accounts
