"""Demonstrates the full lifecycle of an Algorand Standard Asset (ASA).

This maps to the Concepts -> Assets docs page and exercises every ASA
operation: creation, opt-in / opt-out (single and bulk), transfer, reconfigure,
freeze, clawback, queries, and destruction.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.assets``.
"""

from algokit_utils import (
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetOptOutParams,
    AssetTransferParams,
)
from examples._helpers import setup_localnet_environment


def main() -> None:
    algorand, creator, holder = setup_localnet_environment()

    # example: CREATE_ASSET
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=creator.address,
            total=1000,
            decimals=0,
            asset_name="Example Asset",
            unit_name="EX",
            manager=creator.address,
            reserve=creator.address,
            freeze=creator.address,
            clawback=creator.address,
        )
    )
    asset_id = create_result.asset_id
    # example: CREATE_ASSET

    # An account must opt in before it can hold an asset.
    # example: OPT_IN_ASSET
    algorand.send.asset_opt_in(
        AssetOptInParams(
            sender=holder.address,
            asset_id=asset_id,
            signer=holder.signer,
        )
    )
    # example: OPT_IN_ASSET

    # example: TRANSFER_ASSET
    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=creator.address,
            receiver=holder.address,
            asset_id=asset_id,
            amount=100,
        )
    )
    # example: TRANSFER_ASSET

    # Every control address must be specified explicitly on AssetConfigParams;
    # a field left unset is cleared permanently by the protocol at submission.
    # example: RECONFIGURE_ASSET
    algorand.send.asset_config(
        AssetConfigParams(
            sender=creator.address,
            asset_id=asset_id,
            manager=creator.address,
            reserve=creator.address,
            freeze=creator.address,
            clawback=creator.address,
        )
    )
    # example: RECONFIGURE_ASSET

    # example: FREEZE_ASSET
    algorand.send.asset_freeze(
        AssetFreezeParams(
            sender=creator.address,  # the freeze authority
            asset_id=asset_id,
            account=holder.address,
            frozen=True,
        )
    )
    # example: FREEZE_ASSET

    # Unfreeze so the account can participate in the remaining transactions.
    algorand.send.asset_freeze(
        AssetFreezeParams(
            sender=creator.address,
            asset_id=asset_id,
            account=holder.address,
            frozen=False,
        )
    )

    # Clawback is expressed as an asset transfer signed by the clawback
    # authority, with `clawback_target` set to the account the units are
    # pulled from. There is no dedicated clawback params type.
    # example: CLAWBACK_ASSET
    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=creator.address,  # the clawback authority
            receiver=creator.address,
            asset_id=asset_id,
            amount=100,
            clawback_target=holder.address,
        )
    )
    # example: CLAWBACK_ASSET

    # Two throwaway assets to demonstrate the bulk helpers.
    asset_1_id = algorand.send.asset_create(
        AssetCreateParams(sender=creator.address, total=1000, decimals=0, unit_name="B1")
    ).asset_id
    asset_2_id = algorand.send.asset_create(
        AssetCreateParams(sender=creator.address, total=1000, decimals=0, unit_name="B2")
    ).asset_id

    # example: BULK_OPT_IN_ASSET
    algorand.asset.bulk_opt_in(
        account=holder.address,
        asset_ids=[asset_1_id, asset_2_id],
        signer=holder.signer,
    )
    # example: BULK_OPT_IN_ASSET

    # example: BULK_OPT_OUT_ASSET
    algorand.asset.bulk_opt_out(
        account=holder.address,
        asset_ids=[asset_1_id, asset_2_id],
        signer=holder.signer,
    )
    # example: BULK_OPT_OUT_ASSET

    # Opt-out of a single asset (zero balance after the clawback above).
    # example: OPT_OUT_ASSET
    algorand.send.asset_opt_out(
        AssetOptOutParams(
            sender=holder.address,
            asset_id=asset_id,
            creator=creator.address,
            signer=holder.signer,
        )
    )
    # example: OPT_OUT_ASSET

    # example: ASSET_MANAGER_QUERIES
    asset_info = algorand.asset.get_by_id(asset_id)
    creator_holding = algorand.asset.get_account_information(
        creator.address,
        asset_id,
    )
    # example: ASSET_MANAGER_QUERIES

    # Destroy requires all units to sit in the creator account (they do, after
    # the clawback) and the sender to be the current manager.
    # example: DESTROY_ASSET
    algorand.send.asset_destroy(
        AssetDestroyParams(
            sender=creator.address,
            asset_id=asset_id,
        )
    )
    # example: DESTROY_ASSET

    assert asset_info.total == 1000
    assert creator_holding.balance == 1000
    print(f"Exercised full lifecycle for asset {asset_id}")


if __name__ == "__main__":
    main()
