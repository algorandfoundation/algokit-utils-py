from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import algosdk
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.v2client import algod

from algokit_utils.models.account import Account
from algokit_utils.transactions.transaction_composer import (
    AssetOptInParams,
    AssetOptOutParams,
    TransactionComposer,
)


@dataclass(kw_only=True, frozen=True)
class AccountAssetInformation:
    """Information about an account's holding of a particular asset."""

    asset_id: int
    """The ID of the asset."""
    balance: int
    """The amount of the asset held by the account."""
    frozen: bool
    """Whether the asset is frozen for this account."""
    round: int
    """The round this information was retrieved at."""


@dataclass(kw_only=True, frozen=True)
class AssetInformation:
    """Information about an asset."""

    asset_id: int
    """The ID of the asset."""
    creator: str
    """The address of the account that created the asset."""
    total: int
    """The total amount of the smallest divisible units that were created of the asset."""
    decimals: int
    """The amount of decimal places the asset was created with."""
    default_frozen: bool | None = None
    """Whether the asset was frozen by default for all accounts."""
    manager: str | None = None
    """The address of the optional account that can manage the configuration of the asset and destroy it."""
    reserve: str | None = None
    """The address of the optional account that holds the reserve (uncirculated supply) units of the asset."""
    freeze: str | None = None
    """The address of the optional account that can be used to freeze or unfreeze holdings of this asset."""
    clawback: str | None = None
    """The address of the optional account that can clawback holdings of this asset from any account."""
    unit_name: str | None = None
    """The optional name of the unit of this asset (e.g. ticker name)."""
    unit_name_b64: bytes | None = None
    """The optional name of the unit of this asset as bytes."""
    asset_name: str | None = None
    """The optional name of the asset."""
    asset_name_b64: bytes | None = None
    """The optional name of the asset as bytes."""
    url: str | None = None
    """Optional URL where more information about the asset can be retrieved."""
    url_b64: bytes | None = None
    """Optional URL where more information about the asset can be retrieved as bytes."""
    metadata_hash: bytes | None = None
    """32-byte hash of some metadata that is relevant to the asset and/or asset holders."""


@dataclass(kw_only=True, frozen=True)
class BulkAssetOptInOutResult:
    """Individual result from performing a bulk opt-in or bulk opt-out for an account against a series of assets."""

    asset_id: int
    """The ID of the asset opted into / out of"""
    transaction_id: str
    """The transaction ID of the resulting opt in / out"""


class AssetManager:
    """A manager for Algorand assets."""

    def __init__(self, algod_client: algod.AlgodClient, new_group: Callable[[], TransactionComposer]):
        """Create a new asset manager.

        Args:
            algod_client: An algod client
            new_group: A function that creates a new `TransactionComposer` transaction group
        """
        self._algod = algod_client
        self._new_group = new_group

    def get_by_id(self, asset_id: int) -> AssetInformation:
        """Returns the current asset information for the asset with the given ID.

        Args:
            asset_id: The ID of the asset

        Returns:
            The asset information
        """
        asset = self._algod.asset_info(asset_id)
        assert isinstance(asset, dict)
        params = asset["params"]

        return AssetInformation(
            asset_id=asset_id,
            total=params["total"],
            decimals=params["decimals"],
            asset_name=params.get("name"),
            asset_name_b64=params.get("name-b64"),
            unit_name=params.get("unit-name"),
            unit_name_b64=params.get("unit-name-b64"),
            url=params.get("url"),
            url_b64=params.get("url-b64"),
            creator=params["creator"],
            manager=params.get("manager"),
            clawback=params.get("clawback"),
            freeze=params.get("freeze"),
            reserve=params.get("reserve"),
            default_frozen=params.get("default-frozen"),
            metadata_hash=params.get("metadata-hash"),
        )

    def get_account_information(
        self, sender: str | Account | TransactionSigner, asset_id: int
    ) -> AccountAssetInformation:
        """Returns the given sender account's asset holding for a given asset.

        Args:
            sender: The address of the sender/account to look up
            asset_id: The ID of the asset to return a holding for

        Returns:
            The account asset holding information
        """
        address = self._get_address_from_sender(sender)
        info = self._algod.account_asset_info(address, asset_id)
        assert isinstance(info, dict)

        return AccountAssetInformation(
            asset_id=asset_id,
            balance=info["asset-holding"]["amount"],
            frozen=info["asset-holding"]["is-frozen"],
            round=info["round"],
        )

    def bulk_opt_in(
        self,
        account: str | Account | TransactionSigner,
        asset_ids: list[int],
        *,
        suppress_log: bool = False,
        **transaction_params: Any,
    ) -> list[BulkAssetOptInOutResult]:
        """Opt an account in to a list of Algorand Standard Assets.

        Args:
            account: The account to opt-in
            asset_ids: The list of asset IDs to opt-in to
            suppress_log: Whether to suppress logging
            **transaction_params: Any additional transaction parameters

        Returns:
            An array of records matching asset ID to transaction ID of the opt in
        """
        results: list[BulkAssetOptInOutResult] = []
        sender = self._get_address_from_sender(account)

        for asset_group in _chunk_array(asset_ids, algosdk.constants.TX_GROUP_LIMIT):
            composer = self._new_group()

            for asset_id in asset_group:
                params = AssetOptInParams(
                    sender=sender,
                    asset_id=asset_id,
                    **transaction_params,
                )
                composer.add_asset_opt_in(params)

            result = composer.send(suppress_log=suppress_log)

            for i, asset_id in enumerate(asset_group):
                results.append(BulkAssetOptInOutResult(asset_id=asset_id, transaction_id=result.tx_ids[i]))

        return results

    def bulk_opt_out(  # noqa: C901
        self,
        account: str | Account | TransactionSigner,
        asset_ids: list[int],
        *,
        ensure_zero_balance: bool = True,
        suppress_log: bool = False,
        **transaction_params: Any,
    ) -> list[BulkAssetOptInOutResult]:
        """Opt an account out of a list of Algorand Standard Assets.

        Args:
            account: The account to opt-out
            asset_ids: The list of asset IDs to opt-out of
            ensure_zero_balance: Whether to check if the account has a zero balance first
            suppress_log: Whether to suppress logging
            **transaction_params: Any additional transaction parameters

        Returns:
            An array of records matching asset ID to transaction ID of the opt out
        """
        results: list[BulkAssetOptInOutResult] = []
        sender = self._get_address_from_sender(account)

        for asset_group in _chunk_array(asset_ids, algosdk.constants.TX_GROUP_LIMIT):
            composer = self._new_group()

            not_opted_in_asset_ids: list[int] = []
            non_zero_balance_asset_ids: list[int] = []

            if ensure_zero_balance:
                for asset_id in asset_group:
                    try:
                        account_asset_info = self.get_account_information(sender, asset_id)
                        if account_asset_info.balance != 0:
                            non_zero_balance_asset_ids.append(asset_id)
                    except Exception:
                        not_opted_in_asset_ids.append(asset_id)

                if not_opted_in_asset_ids or non_zero_balance_asset_ids:
                    error_message = f"Account {sender}"
                    if not_opted_in_asset_ids:
                        error_message += f" is not opted-in to Asset(s) {', '.join(map(str, not_opted_in_asset_ids))}"
                    if non_zero_balance_asset_ids:
                        error_message += (
                            f" has non-zero balance for Asset(s) {', '.join(map(str, non_zero_balance_asset_ids))}"
                        )
                    error_message += "; can't opt-out."
                    raise ValueError(error_message)

            for asset_id in asset_group:
                asset_info = self.get_by_id(asset_id)
                params = AssetOptOutParams(
                    sender=sender,
                    asset_id=asset_id,
                    creator=asset_info.creator,
                    **transaction_params,
                )
                composer.add_asset_opt_out(params)

            result = composer.send(suppress_log=suppress_log)

            for i, asset_id in enumerate(asset_group):
                results.append(BulkAssetOptInOutResult(asset_id=asset_id, transaction_id=result.tx_ids[i]))

        return results

    @staticmethod
    def _get_address_from_sender(sender: str | Account | TransactionSigner) -> str:
        if isinstance(sender, str):
            return sender
        if isinstance(sender, Account):
            return sender.address
        if isinstance(sender, AccountTransactionSigner):
            return str(algosdk.account.address_from_private_key(sender.private_key))
        raise ValueError(f"Unsupported sender type: {type(sender)}")


def _chunk_array(array: list, size: int) -> list[list]:
    """Split an array into chunks of the given size."""
    return [array[i : i + size] for i in range(0, len(array), size)]
