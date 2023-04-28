import logging
import os
from typing import TYPE_CHECKING, Any

from algosdk.account import address_from_private_key
from algosdk.mnemonic import from_private_key, to_private_key
from algosdk.util import algos_to_microalgos

from algokit_utils._transfer import TransferParameters, transfer
from algokit_utils.models import Account
from algokit_utils.network_clients import get_kmd_client_from_algod_client, is_localnet

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient

__all__ = [
    "create_kmd_wallet_account",
    "get_account",
    "get_account_from_mnemonic",
    "get_dispenser_account",
    "get_kmd_wallet_account",
    "get_localnet_default_account",
    "get_or_create_kmd_wallet_account",
]

logger = logging.getLogger(__name__)
_DEFAULT_ACCOUNT_MINIMUM_BALANCE = 1_000_000_000


def get_account_from_mnemonic(mnemonic: str) -> Account:
    """Convert a mnemonic (25 word passphrase) into an Account"""
    private_key = to_private_key(mnemonic)  # type: ignore[no-untyped-call]
    address = address_from_private_key(private_key)  # type: ignore[no-untyped-call]
    return Account(private_key=private_key, address=address)


def create_kmd_wallet_account(kmd_client: "KMDClient", name: str) -> Account:
    """Creates a wallet with specified name"""
    wallet_id = kmd_client.create_wallet(name, "")["id"]  # type: ignore[no-untyped-call]
    wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")  # type: ignore[no-untyped-call]
    kmd_client.generate_key(wallet_handle)  # type: ignore[no-untyped-call]

    key_ids: list[str] = kmd_client.list_keys(wallet_handle)  # type: ignore[no-untyped-call]
    account_key = key_ids[0]

    private_account_key = kmd_client.export_key(wallet_handle, "", account_key)  # type: ignore[no-untyped-call]
    return get_account_from_mnemonic(from_private_key(private_account_key))  # type: ignore[no-untyped-call]


def get_or_create_kmd_wallet_account(
    client: "AlgodClient", name: str, fund_with_algos: float = 1000, kmd_client: "KMDClient | None" = None
) -> Account:
    """Returns a wallet with specified name, or creates one if not found"""
    kmd_client = kmd_client or get_kmd_client_from_algod_client(client)
    account = get_kmd_wallet_account(client, kmd_client, name)

    if account:
        account_info = client.account_info(account.address)
        assert isinstance(account_info, dict)
        if account_info["amount"] > 0:
            return account
        logger.debug(f"Found existing account in LocalNet with name '{name}', but no funds in the account.")
    else:
        account = create_kmd_wallet_account(kmd_client, name)

        logger.debug(
            f"Couldn't find existing account in LocalNet with name '{name}'. "
            f"So created account {account.address} with keys stored in KMD."
        )

    logger.debug(f"Funding account {account.address} with {fund_with_algos} ALGOs")

    if fund_with_algos:
        transfer(
            client,
            TransferParameters(
                from_account=get_dispenser_account(client),
                to_address=account.address,
                micro_algos=algos_to_microalgos(fund_with_algos),  # type: ignore[no-untyped-call]
            ),
        )

    return account


def _is_default_account(account: dict[str, Any]) -> bool:
    return bool(account["status"] != "Offline" and account["amount"] > _DEFAULT_ACCOUNT_MINIMUM_BALANCE)


def get_localnet_default_account(client: "AlgodClient") -> Account:
    """Returns the default Account in a LocalNet instance"""
    if not is_localnet(client):
        raise Exception("Can't get a default account from non LocalNet network")

    account = get_kmd_wallet_account(
        client, get_kmd_client_from_algod_client(client), "unencrypted-default-wallet", _is_default_account
    )
    assert account
    return account


def get_dispenser_account(client: "AlgodClient") -> Account:
    """Returns an Account based on DISPENSER_MNENOMIC environment variable or the default account on LocalNet"""
    if is_localnet(client):
        return get_localnet_default_account(client)
    return get_account(client, "DISPENSER")


def get_kmd_wallet_account(
    client: "AlgodClient",
    kmd_client: "KMDClient",
    name: str,
    predicate: "Callable[[dict[str, Any]], bool] | None" = None,
) -> Account | None:
    """Returns wallet matching specified name and predicate or None if not found"""
    wallets: list[dict] = kmd_client.list_wallets()  # type: ignore[no-untyped-call]

    wallet = next((w for w in wallets if w["name"] == name), None)
    if wallet is None:
        return None

    wallet_id = wallet["id"]
    wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")  # type: ignore[no-untyped-call]
    key_ids: list[str] = kmd_client.list_keys(wallet_handle)  # type: ignore[no-untyped-call]
    matched_account_key = None
    if predicate:
        for key in key_ids:
            account = client.account_info(key)
            assert isinstance(account, dict)
            if predicate(account):
                matched_account_key = key
    else:
        matched_account_key = next(key_ids.__iter__(), None)

    if not matched_account_key:
        return None

    private_account_key = kmd_client.export_key(wallet_handle, "", matched_account_key)  # type: ignore[no-untyped-call]
    return get_account_from_mnemonic(from_private_key(private_account_key))  # type: ignore[no-untyped-call]


def get_account(
    client: "AlgodClient", name: str, fund_with_algos: float = 1000, kmd_client: "KMDClient | None" = None
) -> Account:
    """Returns an Algorand account with private key loaded by convention based on the given name identifier.

    # Convention

    **Non-LocalNet:** will load `os.environ[f"{name}_MNEMONIC"]` as a mnemonic secret
    Be careful how the mnemonic is handled, never commit it into source control and ideally load it via a
    secret storage service rather than the file system.

    **LocalNet:** will load the account from a KMD wallet called {name} and if that wallet doesn't exist it will
    create it and fund the account for you

    This allows you to write code that will work seamlessly in production and local development (LocalNet) without
    manual config locally (including when you reset the LocalNet).

    # Example
    If you have a mnemonic secret loaded into `os.environ["ACCOUNT_MNEMONIC"]` then you can call the following to get
    that private key loaded into an account object:
    ```python
    account = get_account('ACCOUNT', algod)
    ```

    If that code runs against LocalNet then a wallet called 'ACCOUNT' will automatically be created with an account
    that is automatically funded with 1000 (default) ALGOs from the default LocalNet dispenser.
    """

    mnemonic_key = f"{name.upper()}_MNEMONIC"
    mnemonic = os.getenv(mnemonic_key)
    if mnemonic:
        return get_account_from_mnemonic(mnemonic)

    if is_localnet(client):
        account = get_or_create_kmd_wallet_account(client, name, fund_with_algos, kmd_client)
        os.environ[mnemonic_key] = from_private_key(account.private_key)  # type: ignore[no-untyped-call]
        return account

    raise Exception(f"Missing environment variable '{mnemonic_key}' when looking for account '{name}'")
