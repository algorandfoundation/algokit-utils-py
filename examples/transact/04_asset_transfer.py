# ruff: noqa: N999, C901, PLR0912, PLR0915, PLR2004
"""
Example: Asset Transfer

This example demonstrates the full asset transfer flow using the transact package:
1. Create a new Algorand Standard Asset (ASA)
2. Opt-in: receiver sends 0 amount of the asset to themselves
3. Transfer assets from creator to the opted-in receiver
4. Verify receiver's asset balance after transfer

Uses Transaction wrapper with AssetConfigTransactionFields, AssetTransferTransactionFields,
and PaymentTransactionFields.

Prerequisites:
- LocalNet running (via `algokit localnet start`)
"""

from algokit_transact import (
    AssetConfigTransactionFields,
    AssetTransferTransactionFields,
    PaymentTransactionFields,
    Transaction,
    TransactionType,
    assign_fee,
)
from algokit_utils import AlgorandClient
from examples.shared import (
    create_algod_client,
    print_error,
    print_header,
    print_info,
    print_step,
    print_success,
    shorten_address,
    wait_for_confirmation,
)


def main() -> None:
    print_header("Asset Transfer Example")

    # Step 1: Initialize clients
    print_step(1, "Initialize Algod Client")
    algod = create_algod_client()
    algorand = AlgorandClient.default_localnet()

    try:
        algod.status()
        print_info("Connected to LocalNet Algod")
    except Exception as e:
        print_error(f"Failed to connect to LocalNet: {e}")
        print_info("Make sure LocalNet is running (e.g., algokit localnet start)")
        return

    # Step 2: Get creator account from KMD
    print_step(2, "Get Creator Account from KMD")
    creator = algorand.account.localnet_dispenser()
    print_info(f"Creator address: {shorten_address(creator.addr)}")

    # Step 3: Get suggested transaction parameters
    print_step(3, "Get Suggested Transaction Parameters")
    sp = algod.suggested_params()
    print_info(f"First valid round: {sp.first_valid}")
    print_info(f"Last valid round: {sp.last_valid}")
    print_info(f"Min fee: {sp.min_fee} microALGO")

    # Step 4: Generate and fund receiver account
    print_step(4, "Generate and Fund Receiver Account")

    # Generate a new account for the receiver
    receiver = algorand.account.random()
    print_info(f"Receiver address: {shorten_address(receiver.addr)}")

    # Fund the receiver with enough ALGO to cover transaction fees using low-level transaction
    funding_amount = 1_000_000  # 1 ALGO in microALGO

    fund_tx_without_fee = Transaction(
        transaction_type=TransactionType.Payment,
        sender=creator.addr,
        first_valid=sp.first_valid,
        last_valid=sp.last_valid,
        genesis_hash=sp.genesis_hash,
        genesis_id=sp.genesis_id,
        payment=PaymentTransactionFields(
            receiver=receiver.addr,
            amount=funding_amount,
        ),
    )

    fund_tx = assign_fee(
        fund_tx_without_fee,
        fee_per_byte=sp.fee,
        min_fee=sp.min_fee,
    )

    signed_fund_tx = creator.signer([fund_tx], [0])
    algod.send_raw_transaction(signed_fund_tx[0])
    wait_for_confirmation(algod, fund_tx.tx_id())
    print_info("Funded receiver with 1 ALGO for transaction fees")

    # Step 5: Create a new asset
    print_step(5, "Create New Asset")

    # Asset parameters
    asset_total = 10_000_000_000  # 10,000 units with 6 decimals
    asset_decimals = 6
    asset_name = "Transfer Test Token"
    asset_unit_name = "TTT"

    display_total = asset_total / (10**asset_decimals)
    print_info(f"Creating asset: {asset_name} ({asset_unit_name})")
    print_info(f"Total supply: {asset_total} ({display_total:,.0f} {asset_unit_name})")

    # Create asset config transaction
    create_asset_tx_without_fee = Transaction(
        transaction_type=TransactionType.AssetConfig,
        sender=creator.addr,
        first_valid=sp.first_valid,
        last_valid=sp.last_valid,
        genesis_hash=sp.genesis_hash,
        genesis_id=sp.genesis_id,
        asset_config=AssetConfigTransactionFields(
            asset_id=0,  # 0 indicates asset creation
            total=asset_total,
            decimals=asset_decimals,
            default_frozen=False,
            asset_name=asset_name,
            unit_name=asset_unit_name,
            url="https://example.com/transfer-token",
            manager=creator.addr,
            reserve=creator.addr,
            freeze=creator.addr,
            clawback=creator.addr,
        ),
    )

    create_asset_tx = assign_fee(
        create_asset_tx_without_fee,
        fee_per_byte=sp.fee,
        min_fee=sp.min_fee,
    )

    # Sign and submit asset creation transaction
    signed_create_tx = creator.signer([create_asset_tx], [0])
    create_tx_id = create_asset_tx.tx_id()
    algod.send_raw_transaction(signed_create_tx[0])
    print_info(f"Asset creation transaction submitted: {create_tx_id}")

    create_pending_info = wait_for_confirmation(algod, create_tx_id)
    asset_id = create_pending_info.asset_id
    if not asset_id:
        raise ValueError("Asset ID not found in pending transaction response")
    print_info(f"Asset created with ID: {asset_id}")
    print_success(f"Asset {asset_name} (ID: {asset_id}) created successfully!")

    # Step 6: Opt-in - Receiver sends 0 amount to themselves
    print_step(6, "Opt-in: Receiver Opts Into the Asset")
    print_info("Opt-in is done by sending 0 amount of the asset to yourself")

    # Refresh suggested params for the new transaction
    opt_in_sp = algod.suggested_params()

    opt_in_tx_without_fee = Transaction(
        transaction_type=TransactionType.AssetTransfer,
        sender=receiver.addr,  # Receiver is the sender for opt-in
        first_valid=opt_in_sp.first_valid,
        last_valid=opt_in_sp.last_valid,
        genesis_hash=opt_in_sp.genesis_hash,
        genesis_id=opt_in_sp.genesis_id,
        asset_transfer=AssetTransferTransactionFields(
            asset_id=asset_id,
            receiver=receiver.addr,  # Receiver sends to themselves
            amount=0,  # 0 amount for opt-in
        ),
    )

    opt_in_tx = assign_fee(
        opt_in_tx_without_fee,
        fee_per_byte=opt_in_sp.fee,
        min_fee=opt_in_sp.min_fee,
    )

    # Sign and submit opt-in transaction
    signed_opt_in_tx = receiver.signer([opt_in_tx], [0])
    opt_in_tx_id = opt_in_tx.tx_id()
    algod.send_raw_transaction(signed_opt_in_tx[0])
    print_info(f"Opt-in transaction submitted: {opt_in_tx_id}")

    wait_for_confirmation(algod, opt_in_tx_id)
    print_info(f"Receiver opted into asset ID: {asset_id}")
    print_success("Receiver successfully opted into the asset!")

    # Verify receiver has 0 balance after opt-in
    receiver_asset_info_after_opt_in = algod.account_asset_information(receiver.addr, asset_id)
    balance_after_opt_in = receiver_asset_info_after_opt_in.asset_holding.amount
    print_info(f"Receiver asset balance after opt-in: {balance_after_opt_in}")

    # Step 7: Transfer assets from creator to receiver
    print_step(7, "Transfer Assets from Creator to Receiver")

    transfer_amount = 1_000_000_000  # 1,000 units (with 6 decimals)
    display_transfer = transfer_amount / (10**asset_decimals)
    print_info(f"Transferring {transfer_amount} ({display_transfer:,.0f} {asset_unit_name}) to receiver")

    # Refresh suggested params for the transfer transaction
    transfer_sp = algod.suggested_params()

    transfer_tx_without_fee = Transaction(
        transaction_type=TransactionType.AssetTransfer,
        sender=creator.addr,  # Creator sends the assets
        first_valid=transfer_sp.first_valid,
        last_valid=transfer_sp.last_valid,
        genesis_hash=transfer_sp.genesis_hash,
        genesis_id=transfer_sp.genesis_id,
        asset_transfer=AssetTransferTransactionFields(
            asset_id=asset_id,
            receiver=receiver.addr,
            amount=transfer_amount,
        ),
    )

    transfer_tx = assign_fee(
        transfer_tx_without_fee,
        fee_per_byte=transfer_sp.fee,
        min_fee=transfer_sp.min_fee,
    )

    # Sign and submit transfer transaction
    signed_transfer_tx = creator.signer([transfer_tx], [0])
    transfer_tx_id = transfer_tx.tx_id()
    algod.send_raw_transaction(signed_transfer_tx[0])
    print_info(f"Transfer transaction submitted: {transfer_tx_id}")

    wait_for_confirmation(algod, transfer_tx_id)
    print_success(f"Transferred {display_transfer:,.0f} {asset_unit_name} to receiver!")

    # Step 8: Verify receiver's asset balance after transfer
    print_step(8, "Verify Receiver Asset Balance After Transfer")

    receiver_asset_info_after_transfer = algod.account_asset_information(receiver.addr, asset_id)
    receiver_balance = receiver_asset_info_after_transfer.asset_holding.amount
    display_receiver_balance = receiver_balance / (10**asset_decimals)
    print_info(f"Receiver asset balance: {receiver_balance} ({display_receiver_balance:,.0f} {asset_unit_name})")

    if receiver_balance != transfer_amount:
        raise ValueError(f"Balance mismatch: expected {transfer_amount}, got {receiver_balance}")
    print_success(f"Receiver balance verified: {display_receiver_balance:,.0f} {asset_unit_name}")

    # Also verify creator's remaining balance
    creator_asset_info_after_transfer = algod.account_asset_information(creator.addr, asset_id)
    creator_balance = creator_asset_info_after_transfer.asset_holding.amount
    expected_creator_balance = asset_total - transfer_amount
    display_creator_balance = creator_balance / (10**asset_decimals)
    print_info(f"Creator remaining balance: {creator_balance} ({display_creator_balance:,.0f} {asset_unit_name})")

    if creator_balance != expected_creator_balance:
        raise ValueError(f"Creator balance mismatch: expected {expected_creator_balance}, got {creator_balance}")
    print_success(f"Creator balance verified: {display_creator_balance:,.0f} {asset_unit_name}")

    print_success("Asset transfer example completed successfully!")


if __name__ == "__main__":
    main()
