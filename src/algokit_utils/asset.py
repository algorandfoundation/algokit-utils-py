import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

from algokit_utils import Account, TransferAssetParameters, transfer_asset

__all__ = ["opt_in"]
logger = logging.getLogger(__name__)


def opt_in(algod_client: "AlgodClient", account: Account, asset_id: int) -> None:
    transfer_asset(
        algod_client,
        TransferAssetParameters(
            from_account=account,
            to_address=account.address,
            asset_id=asset_id,
            amount=0,
            note=f"Opt in asset id ${asset_id}",
        ),
    )


def opt_out(algod_client: "AlgodClient", account: Account, asset_id: int) -> None:
    asset = algod_client.account_asset_info(account.address, asset_id)
    transfer_asset(
        algod_client,
        TransferAssetParameters(
            from_account=account,
            to_address=account.address,
            asset_id=asset_id,
            amount=0,
            note=f"Opt in asset id ${asset_id}",
            close_assets_to=asset["params"]["creator"],  # type: ignore
        ),
    )
