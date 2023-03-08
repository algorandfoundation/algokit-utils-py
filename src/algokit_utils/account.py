import logging
import os
from collections.abc import Callable
from typing import Any

from algosdk.account import address_from_private_key
from algosdk.kmd import KMDClient
from algosdk.mnemonic import from_private_key, to_private_key
from algosdk.util import algos_to_microalgos
from algosdk.v2client.algod import AlgodClient

from algokit_utils.models import Account
from algokit_utils.network_clients import get_kmd_client_from_algod_client, is_sandbox
from algokit_utils.transfer import TransferParameters, transfer

logger = logging.getLogger(__name__)


def get_account_from_mnemonic(mnemonic: str) -> Account:
    private_key = to_private_key(mnemonic)  # type: ignore[no-untyped-call]
    address = address_from_private_key(private_key)  # type: ignore[no-untyped-call]
    return Account(private_key, address)


def get_or_create_kmd_wallet_account(
    client: AlgodClient, name: str, fund_with: int | None, kmd_client: KMDClient | None = None
) -> Account:
    kmd_client = kmd_client or get_kmd_client_from_algod_client(client)
    fund_with = 1000 if fund_with is None else fund_with
    account = get_kmd_wallet_account(client, kmd_client, name)

    if account:
        account_info = client.account_info(account.address)  # type: ignore[no-untyped-call]
        if account_info["amount"] > 0:
            return account
        logger.debug(f"Found existing account in Sandbox with name '{name}'." f"But no funds in the account.")
    else:
        wallet_id = kmd_client.create_wallet(name, "")["id"]  # type: ignore[no-untyped-call]
        wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")  # type: ignore[no-untyped-call]
        kmd_client.generate_key(wallet_handle)  # type: ignore[no-untyped-call]

        account = get_kmd_wallet_account(client, kmd_client, name)
        assert account
        logger.debug(
            f"Couldn't find existing account in Sandbox with name '{name}'. "
            f"So created account {account.address} with keys stored in KMD."
        )

    logger.debug(f"Funding account {account.address} with {fund_with} ALGOs")

    transfer(
        TransferParameters(
            from_account=get_dispenser_account(client),
            to_address=account.address,
            amount=algos_to_microalgos(fund_with),  # type: ignore[no-untyped-call]
        ),
        client,
    )

    return account


def _is_default_account(account: dict[str, Any]) -> bool:
    return bool(account["status"] != "Offline" and account["amount"] > 1_000_000_000)


def get_sandbox_default_account(client: AlgodClient) -> Account:
    if not is_sandbox(client):
        raise Exception("Can't get a default account from non Sandbox network")

    account = get_kmd_wallet_account(
        client, get_kmd_client_from_algod_client(client), "unencrypted-default-wallet", _is_default_account
    )
    assert account
    return account


def get_dispenser_account(client: AlgodClient) -> Account:
    if is_sandbox(client):
        return get_sandbox_default_account(client)
    return get_account(client, "DISPENSER")


def get_kmd_wallet_account(
    client: AlgodClient, kmd_client: KMDClient, name: str, predicate: Callable[[dict[str, Any]], bool] | None = None
) -> Account | None:
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
            account = client.account_info(key)  # type: ignore[no-untyped-call]
            if predicate(account):
                matched_account_key = key
    else:
        matched_account_key = next(key_ids.__iter__(), None)

    if not matched_account_key:
        return None

    private_account_key = kmd_client.export_key(wallet_handle, "", matched_account_key)  # type: ignore[no-untyped-call]
    return get_account_from_mnemonic(from_private_key(private_account_key))  # type: ignore[no-untyped-call]


def get_account(
    client: AlgodClient, name: str, fund_with: int | None = None, kmd_client: KMDClient | None = None
) -> Account:
    mnemonic_key = f"{name.upper()}_MNEMONIC"
    mnemonic = os.getenv(mnemonic_key)
    if mnemonic:
        return get_account_from_mnemonic(mnemonic)

    if is_sandbox(client):
        account = get_or_create_kmd_wallet_account(client, name, fund_with, kmd_client)
        os.environ[mnemonic_key] = account.private_key
        return account

    raise Exception(f"Missing environment variable '{mnemonic_key}' when looking for account '{name}'")
