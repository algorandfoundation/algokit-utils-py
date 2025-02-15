from collections.abc import Callable
from dataclasses import dataclass

import algosdk
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.v2client import algod

from algokit_utils.models.account import SigningAccount
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.models.transaction import SendParams
from algokit_utils.transactions.transaction_composer import (
    AssetOptInParams,
    AssetOptOutParams,
    TransactionComposer,
)

__all__ = ["AccountAssetInformation", "AssetInformation", "AssetManager", "BulkAssetOptInOutResult"]


@dataclass(kw_only=True, frozen=True)
class AccountAssetInformation:
    """Information about an account's holding of a particular asset."""

    asset_id: int
    """The ID of the asset"""
    balance: int
    """The amount of the asset held by the account"""
    frozen: bool
    """Whether the asset is frozen for this account"""
    round: int
    """The round this information was retrieved at"""


@dataclass(kw_only=True, frozen=True)
class AssetInformation:
    """Information about an Algorand Standard Asset (ASA)."""

    asset_id: int
    """The ID of the asset"""
    creator: str
    """The address of the account that created the asset"""
    total: int
    """The total amount of the smallest divisible units that were created of the asset"""
    decimals: int
    """The amount of decimal places the asset was created with"""
    default_frozen: bool | None = None
    """Whether the asset was frozen by default for all accounts, defaults to None"""
    manager: str | None = None
    """The address of the optional account that can manage the configuration of the asset and destroy it,
        defaults to None"""
    reserve: str | None = None
    """The address of the optional account that holds the reserve (uncirculated supply) units of the asset,
        defaults to None"""
    freeze: str | None = None
    """The address of the optional account that can be used to freeze or unfreeze holdings of this asset,
        defaults to None"""
    clawback: str | None = None
    """The address of the optional account that can clawback holdings of this asset from any account,
        defaults to None"""
    unit_name: str | None = None
    """The optional name of the unit of this asset (e.g. ticker name), defaults to None"""
    unit_name_b64: bytes | None = None
    """The optional name of the unit of this asset as bytes, defaults to None"""
    asset_name: str | None = None
    """The optional name of the asset, defaults to None"""
    asset_name_b64: bytes | None = None
    """The optional name of the asset as bytes, defaults to None"""
    url: str | None = None
    """The optional URL where more information about the asset can be retrieved, defaults to None"""
    url_b64: bytes | None = None
    """The optional URL where more information about the asset can be retrieved as bytes, defaults to None"""
    metadata_hash: bytes | None = None
    """The 32-byte hash of some metadata that is relevant to the asset and/or asset holders, defaults to None"""


@dataclass(kw_only=True, frozen=True)
class BulkAssetOptInOutResult:
    """Result from performing a bulk opt-in or bulk opt-out for an account against a series of assets.

    :ivar asset_id: The ID of the asset opted into / out of
    :ivar transaction_id: The transaction ID of the resulting opt in / out
    """

    asset_id: int
    """The ID of the asset opted into / out of"""
    transaction_id: str
    """The transaction ID of the resulting opt in / out"""


class AssetManager:
    """A manager for Algorand Standard Assets (ASAs).

    :param algod_client: An algod client
    :param new_group: A function that creates a new TransactionComposer transaction group

    :example:
        >>> asset_manager = AssetManager(algod_client)
    """

    def __init__(self, algod_client: algod.AlgodClient, new_group: Callable[[], TransactionComposer]):
        self._algod = algod_client
        self._new_group = new_group

    def get_by_id(self, asset_id: int) -> AssetInformation:
        """Returns the current asset information for the asset with the given ID.

        :param asset_id: The ID of the asset
        :return: The asset information

        :example:
            >>> asset_manager = AssetManager(algod_client)
            >>> asset_info = asset_manager.get_by_id(1234567890)
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
        self, sender: str | SigningAccount | TransactionSigner, asset_id: int
    ) -> AccountAssetInformation:
        """Returns the given sender account's asset holding for a given asset.

        :param sender: The address of the sender/account to look up
        :param asset_id: The ID of the asset to return a holding for
        :return: The account asset holding information

        :example:
            >>> asset_manager = AssetManager(algod_client)
            >>> account_asset_info = asset_manager.get_account_information(sender, asset_id)
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

    def bulk_opt_in(  # noqa: PLR0913
        self,
        account: str,
        asset_ids: list[int],
        signer: TransactionSigner | None = None,
        rekey_to: str | None = None,
        note: bytes | None = None,
        lease: bytes | None = None,
        static_fee: AlgoAmount | None = None,
        extra_fee: AlgoAmount | None = None,
        max_fee: AlgoAmount | None = None,
        validity_window: int | None = None,
        first_valid_round: int | None = None,
        last_valid_round: int | None = None,
        send_params: SendParams | None = None,
    ) -> list[BulkAssetOptInOutResult]:
        """Opt an account in to a list of Algorand Standard Assets.

        :param account: The account to opt-in
        :param asset_ids: The list of asset IDs to opt-in to
        :param signer: The signer to use for the transaction, defaults to None
        :param rekey_to: The address to rekey the account to, defaults to None
        :param note: The note to include in the transaction, defaults to None
        :param lease: The lease to include in the transaction, defaults to None
        :param static_fee: The static fee to include in the transaction, defaults to None
        :param extra_fee: The extra fee to include in the transaction, defaults to None
        :param max_fee: The maximum fee to include in the transaction, defaults to None
        :param validity_window: The validity window to include in the transaction, defaults to None
        :param first_valid_round: The first valid round to include in the transaction, defaults to None
        :param last_valid_round: The last valid round to include in the transaction, defaults to None
        :param send_params: The send parameters to use for the transaction, defaults to None
        :return: An array of records matching asset ID to transaction ID of the opt in

        :example:
            >>> asset_manager = AssetManager(algod_client)
            >>> results = asset_manager.bulk_opt_in(account, asset_ids)
        """
        results: list[BulkAssetOptInOutResult] = []
        sender = self._get_address_from_sender(account)

        for asset_group in _chunk_array(asset_ids, algosdk.constants.TX_GROUP_LIMIT):
            composer = self._new_group()

            for asset_id in asset_group:
                params = AssetOptInParams(
                    sender=sender,
                    asset_id=asset_id,
                    signer=signer,
                    rekey_to=rekey_to,
                    note=note,
                    lease=lease,
                    static_fee=static_fee,
                    extra_fee=extra_fee,
                    max_fee=max_fee,
                    validity_window=validity_window,
                    first_valid_round=first_valid_round,
                    last_valid_round=last_valid_round,
                )
                composer.add_asset_opt_in(params)

            result = composer.send(send_params)

            for i, asset_id in enumerate(asset_group):
                results.append(BulkAssetOptInOutResult(asset_id=asset_id, transaction_id=result.tx_ids[i]))

        return results

    def bulk_opt_out(  # noqa: C901, PLR0913
        self,
        *,
        account: str,
        asset_ids: list[int],
        ensure_zero_balance: bool = True,
        signer: TransactionSigner | None = None,
        rekey_to: str | None = None,
        note: bytes | None = None,
        lease: bytes | None = None,
        static_fee: AlgoAmount | None = None,
        extra_fee: AlgoAmount | None = None,
        max_fee: AlgoAmount | None = None,
        validity_window: int | None = None,
        first_valid_round: int | None = None,
        last_valid_round: int | None = None,
        send_params: SendParams | None = None,
    ) -> list[BulkAssetOptInOutResult]:
        """Opt an account out of a list of Algorand Standard Assets.

        :param account: The account to opt-out
        :param asset_ids: The list of asset IDs to opt-out of
        :param ensure_zero_balance: Whether to check if the account has a zero balance first, defaults to True
        :param signer: The signer to use for the transaction, defaults to None
        :param rekey_to: The address to rekey the account to, defaults to None
        :param note: The note to include in the transaction, defaults to None
        :param lease: The lease to include in the transaction, defaults to None
        :param static_fee: The static fee to include in the transaction, defaults to None
        :param extra_fee: The extra fee to include in the transaction, defaults to None
        :param max_fee: The maximum fee to include in the transaction, defaults to None
        :param validity_window: The validity window to include in the transaction, defaults to None
        :param first_valid_round: The first valid round to include in the transaction, defaults to None
        :param last_valid_round: The last valid round to include in the transaction, defaults to None
        :param send_params: The send parameters to use for the transaction, defaults to None
        :raises ValueError: If ensure_zero_balance is True and account has non-zero balance or is not opted in
        :return: An array of records matching asset ID to transaction ID of the opt out

        :example:
            >>> asset_manager = AssetManager(algod_client)
            >>> results = asset_manager.bulk_opt_out(account, asset_ids)
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
                    signer=signer,
                    rekey_to=rekey_to,
                    note=note,
                    lease=lease,
                    static_fee=static_fee,
                    extra_fee=extra_fee,
                    max_fee=max_fee,
                    validity_window=validity_window,
                    first_valid_round=first_valid_round,
                    last_valid_round=last_valid_round,
                )
                composer.add_asset_opt_out(params)

            result = composer.send(send_params)

            for i, asset_id in enumerate(asset_group):
                results.append(BulkAssetOptInOutResult(asset_id=asset_id, transaction_id=result.tx_ids[i]))

        return results

    @staticmethod
    def _get_address_from_sender(sender: str | SigningAccount | TransactionSigner) -> str:
        if isinstance(sender, str):
            return sender
        if isinstance(sender, SigningAccount):
            return sender.address
        if isinstance(sender, AccountTransactionSigner):
            return str(algosdk.account.address_from_private_key(sender.private_key))
        raise ValueError(f"Unsupported sender type: {type(sender)}")


def _chunk_array(array: list, size: int) -> list[list]:
    return [array[i : i + size] for i in range(0, len(array), size)]
