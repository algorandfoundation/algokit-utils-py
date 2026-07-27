"""Demonstrates creating an Algorand Standard Asset, opting in and transferring it.

This maps to the Concepts -> Assets docs page.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.assets``.
"""

from algokit_utils import AssetCreateParams, AssetOptInParams, AssetTransferParams
from examples._helpers import setup_localnet_environment


def main() -> None:
    env = setup_localnet_environment()
    algorand, account_a, account_b = env

    # example: CREATE_ASSET
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=account_a.address,
            total=1000,
            decimals=0,
            asset_name="Example Asset",
            unit_name="EX",
        )
    )
    asset_id = create_result.asset_id
    # example: CREATE_ASSET

    # An account must opt in before it can hold an asset.
    # example: OPT_IN_ASSET
    algorand.send.asset_opt_in(AssetOptInParams(sender=account_b.address, asset_id=asset_id, signer=account_b.signer))
    # example: OPT_IN_ASSET

    # example: TRANSFER_ASSET
    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=account_a.address,
            receiver=account_b.address,
            asset_id=asset_id,
            amount=100,
        )
    )
    # example: TRANSFER_ASSET

    holding = algorand.asset.get_account_information(account_b.address, asset_id)
    assert holding.balance == 100
    print(f"Created asset {asset_id} and transferred 100 units to {account_b.address}")


if __name__ == "__main__":
    main()
