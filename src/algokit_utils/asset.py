from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

from algokit_utils import Account, TransferAssetParameters, transfer_asset


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
