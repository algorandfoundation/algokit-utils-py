"""Demonstrates the full lifecycle of an Algorand Standard Asset (ASA).

This maps to the Concepts -> Assets docs page and exercises every ASA
operation: creation, opt-in / opt-out (single and bulk), transfer, reconfigure,
freeze, clawback, queries, and destruction.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.assets``.
"""

from algokit_utils import (
    AlgoAmount,
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
    env = setup_localnet_environment()
    algorand, account_a, account_b = env

    # A third funded account is used to demonstrate bulk opt-in and bulk
    # opt-out against a fresh pair of assets.
    dispenser = algorand.account.localnet_dispenser()
    account_c = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=account_c.address,
        dispenser_account=dispenser.address,
        min_spending_balance=AlgoAmount.from_algo(10),
    )

    # example: CREATE_ASSET
    create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=account_a.address,
            total=1000,
            decimals=0,
            asset_name="Example Asset",
            unit_name="EX",
            manager=account_a.address,
            reserve=account_a.address,
            freeze=account_a.address,
            clawback=account_a.address,
        )
    )
    asset_id = create_result.asset_id
    # example: CREATE_ASSET

    # An account must opt in before it can hold an asset.
    # example: OPT_IN_ASSET
    algorand.send.asset_opt_in(
        AssetOptInParams(
            sender=account_b.address,
            asset_id=asset_id,
            signer=account_b.signer,
        )
    )
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

    # Every control address must be specified explicitly on AssetConfigParams;
    # a field left unset is cleared permanently by the protocol at submission.
    # example: RECONFIGURE_ASSET
    algorand.send.asset_config(
        AssetConfigParams(
            sender=account_a.address,
            asset_id=asset_id,
            manager=account_a.address,
            reserve=account_a.address,
            freeze=account_a.address,
            clawback=account_a.address,
        )
    )
    # example: RECONFIGURE_ASSET

    # example: FREEZE_ASSET
    algorand.send.asset_freeze(
        AssetFreezeParams(
            sender=account_a.address,
            asset_id=asset_id,
            account=account_b.address,
            frozen=True,
        )
    )
    # example: FREEZE_ASSET

    # Unfreeze so the account can participate in the remaining transactions.
    algorand.send.asset_freeze(
        AssetFreezeParams(
            sender=account_a.address,
            asset_id=asset_id,
            account=account_b.address,
            frozen=False,
        )
    )

    # Clawback is expressed as an asset transfer signed by the clawback
    # authority, with `clawback_target` set to the account the units are
    # pulled from. There is no dedicated clawback params type.
    # example: CLAWBACK_ASSET
    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=account_a.address,
            receiver=account_a.address,
            asset_id=asset_id,
            amount=100,
            clawback_target=account_b.address,
        )
    )
    # example: CLAWBACK_ASSET

    # Two more assets to demonstrate the bulk helpers against a fresh account.
    bulk_asset_ids = [
        algorand.send.asset_create(
            AssetCreateParams(sender=account_a.address, total=1000, decimals=0, unit_name="B1")
        ).asset_id,
        algorand.send.asset_create(
            AssetCreateParams(sender=account_a.address, total=1000, decimals=0, unit_name="B2")
        ).asset_id,
    ]

    # example: BULK_OPT_IN_ASSET
    algorand.asset.bulk_opt_in(
        account=account_c.address,
        asset_ids=bulk_asset_ids,
        signer=account_c.signer,
    )
    # example: BULK_OPT_IN_ASSET

    # example: BULK_OPT_OUT_ASSET
    algorand.asset.bulk_opt_out(
        account=account_c.address,
        asset_ids=bulk_asset_ids,
        signer=account_c.signer,
    )
    # example: BULK_OPT_OUT_ASSET

    # Opt-out of a single asset (zero balance after the clawback above).
    # example: OPT_OUT_ASSET
    algorand.send.asset_opt_out(
        AssetOptOutParams(
            sender=account_b.address,
            asset_id=asset_id,
            creator=account_a.address,
            signer=account_b.signer,
        )
    )
    # example: OPT_OUT_ASSET

    # example: ASSET_MANAGER_QUERIES
    asset_info = algorand.asset.get_by_id(asset_id)
    creator_holding = algorand.asset.get_account_information(
        account_a.address,
        asset_id,
    )
    # example: ASSET_MANAGER_QUERIES

    # Destroy requires all units to sit in the creator account (they do, after
    # the clawback) and the sender to be the current manager.
    # example: DESTROY_ASSET
    algorand.send.asset_destroy(
        AssetDestroyParams(
            sender=account_a.address,
            asset_id=asset_id,
        )
    )
    # example: DESTROY_ASSET

    assert asset_info.total == 1000
    assert creator_holding.balance == 1000
    print(f"Exercised full lifecycle for asset {asset_id}")


if __name__ == "__main__":
    main()
