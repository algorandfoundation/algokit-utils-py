import logging
from typing import TYPE_CHECKING

from algosdk.atomic_transaction_composer import AtomicTransactionComposer, TransactionWithSigner
from algosdk.constants import TX_GROUP_LIMIT
from algosdk.transaction import AssetTransferTxn

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

from algokit_utils.models import Account

__all__ = ["opt_in", "opt_out"]
logger = logging.getLogger(__name__)


def _ensure_asset_balance(algod_client: "AlgodClient", account: Account, asset_ids: list) -> None:
    invalid_asset_ids = []
    for asset_id in asset_ids:
        try:
            account_asset_info = algod_client.account_asset_info(account.address, asset_id)
            if account_asset_info["asset-holding"]["amount"] != 0:  # type: ignore  # noqa: PGH003
                logger.debug(f"Asset {asset_id} balance is not zero")
                invalid_asset_ids.append(asset_id)
        except Exception:
            logger.debug(f"Account ${account.address} does not have asset ${asset_id}")
            invalid_asset_ids.append(asset_id)

    if len(invalid_asset_ids) > 0:
        raise ValueError(
            f" Assets {invalid_asset_ids} cannot be opted out. Ensure that their amount is zero and that the account "
            "has previously opted into them."
        )


def _ensure_asset_first_optin(algod_client: "AlgodClient", account: Account, asset_ids: list) -> None:
    invalid_asset_ids = []
    for asset_id in asset_ids:
        try:
            account_info = algod_client.account_info(account.address)
            asset_exists_in_account_info = any(
                asset["asset-id"] == asset_id for asset in account_info["assets"]  # type: ignore  # noqa: PGH003
            )
            if asset_exists_in_account_info:
                logger.debug(f"Asset {asset_id} is already opted in for account {account.address}")
                invalid_asset_ids.append(asset_id)
        except Exception:
            logger.debug("Unable to get account info. Account address supplied does not exist")
            invalid_asset_ids.append(asset_id)

    if len(invalid_asset_ids) > 0:
        raise ValueError(
            f" Assets {invalid_asset_ids} cannot be opted in. Ensure that they are valid and that the "
            "account has not previously opted into them."
        )


def opt_in(algod_client: "AlgodClient", account: Account, asset_ids: list[int]) -> dict[int, str]:
    """
    Opt-in to a list of assets on the Algorand blockchain. Before an account can receive a specific asset,
    it must `opt-in` to receive it. An opt-in transaction places an asset holding of 0 into the account and increases
    its minimum balance by [100,000 microAlgos](https://developer.algorand.org/docs/get-details/asa/#assets-overview).

    Args:
        algod_client (AlgodClient): An instance of the AlgodClient class from the algosdk library.
        account (Account): An instance of the Account class representing the account that wants to opt-in to the assets.
        asset_ids (list[int]): A list of integers representing the asset IDs to opt-in to.
    Returns:
        dict[int, str]: A dictionary where the keys are the asset IDs and the values
        are the transaction IDs for opting-in to each asset.
    """
    _ensure_asset_first_optin(algod_client, account, asset_ids)
    suggested_params = algod_client.suggested_params()
    result = {}
    for i in range(0, len(asset_ids), TX_GROUP_LIMIT):
        atc = AtomicTransactionComposer()
        chunk = asset_ids[i : i + TX_GROUP_LIMIT]
        for asset_id in chunk:
            asset = algod_client.asset_info(asset_id)
            xfer_txn = AssetTransferTxn(
                sp=suggested_params,
                sender=account.address,
                receiver=account.address,
                close_assets_to=None,
                revocation_target=None,
                amt=0,
                note=f"opt in asset id ${asset_id}",
                index=asset["index"],  # type: ignore  # noqa: PGH003
                rekey_to=None,
            )

            transaction_with_signer = TransactionWithSigner(
                txn=xfer_txn,
                signer=account.signer,
            )
            atc.add_transaction(transaction_with_signer)
        atc.execute(algod_client, 4)

        for index, asset_id in enumerate(chunk):
            result[asset_id] = atc.tx_ids[index]

    return result


def opt_out(algod_client: "AlgodClient", account: Account, asset_ids: list[int]) -> dict[int, str]:
    """
    Opt out from a list of Algorand Standard Assets (ASAs) by transferring them back to their creators.
    The account also recovers the Minimum Balance Requirement for the asset (100,000 microAlgos)
    The `optOut` function manages the opt-out process, permitting the account to discontinue holding a group of assets.

    It's essential to note that an account can only opt_out of an asset if its balance of that asset is zero.

    Args:
        algod_client (AlgodClient): An instance of the AlgodClient class from the `algosdk` library.
        account (Account): An instance of the Account class that holds the private key and address for an account.
        asset_ids (list[int]): A list of integers representing the asset IDs of the ASAs to opt out from.
    Returns:
        dict[int, str]: A dictionary where the keys are the asset IDs and the values are the transaction IDs of
        the executed transactions.

    """
    _ensure_asset_balance(algod_client, account, asset_ids)
    suggested_params = algod_client.suggested_params()
    result = {}
    for i in range(0, len(asset_ids), TX_GROUP_LIMIT):
        atc = AtomicTransactionComposer()
        chunk = asset_ids[i : i + TX_GROUP_LIMIT]
        for asset_id in chunk:
            asset = algod_client.asset_info(asset_id)
            asset_creator = asset["params"]["creator"]  # type: ignore  # noqa: PGH003
            xfer_txn = AssetTransferTxn(
                sp=suggested_params,
                sender=account.address,
                receiver=account.address,
                close_assets_to=asset_creator,
                revocation_target=None,
                amt=0,
                note=f"opt out asset id ${asset_id}",
                index=asset["index"],  # type: ignore  # noqa: PGH003
                rekey_to=None,
            )

            transaction_with_signer = TransactionWithSigner(
                txn=xfer_txn,
                signer=account.signer,
            )
            atc.add_transaction(transaction_with_signer)
        atc.execute(algod_client, 4)

        for index, asset_id in enumerate(chunk):
            result[asset_id] = atc.tx_ids[index]

    return result
