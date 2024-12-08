from typing import Any, cast

from algosdk import logic, transaction
from algosdk.atomic_transaction_composer import AtomicTransactionComposer, EmptySigner, TransactionWithSigner
from algosdk.box_reference import BoxReference
from algosdk.error import AtomicTransactionComposerError
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.models import SimulateRequest

# Constants
MAX_APP_CALL_ACCOUNT_REFERENCES = 4
MAX_APP_CALL_FOREIGN_REFERENCES = 8


def populate_app_call_resources(atc: AtomicTransactionComposer, algod: AlgodClient) -> AtomicTransactionComposer:
    """
    Populate application call resources based on simulation results.
    """
    # Get unnamed resources from simulation
    unnamed_resources = get_unnamed_app_call_resources_accessed(atc, algod)
    group = atc.build_group()

    # Process transaction-level resources
    for i, txn_resources in enumerate(unnamed_resources["txns"]):
        if not txn_resources or not isinstance(group[i].txn, transaction.ApplicationCallTxn):
            continue

        # Validate no unexpected resources
        if txn_resources.get("boxes") or txn_resources.get("extraBoxRefs"):
            raise ValueError("Unexpected boxes at the transaction level")
        if txn_resources.get("appLocals"):
            raise ValueError("Unexpected app local at the transaction level")
        if txn_resources.get("assetHoldings"):
            raise ValueError("Unexpected asset holding at the transaction level")

        # Update application call fields
        app_txn = cast(transaction.ApplicationCallTxn, group[i].txn)
        accounts = list(getattr(app_txn, "accounts", []) or [])
        foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
        foreign_assets = list(getattr(app_txn, "foreign_assets", []) or [])
        boxes = list(getattr(app_txn, "boxes", []) or [])

        # Add new resources
        accounts.extend(txn_resources.get("accounts", []))
        foreign_apps.extend(txn_resources.get("apps", []))
        foreign_assets.extend(txn_resources.get("assets", []))
        boxes.extend(txn_resources.get("boxes", []))

        # Validate limits
        if len(accounts) > MAX_APP_CALL_ACCOUNT_REFERENCES:
            raise ValueError(
                f"Account reference limit of {MAX_APP_CALL_ACCOUNT_REFERENCES} exceeded in transaction {i}"
            )

        total_refs = len(accounts) + len(foreign_assets) + len(foreign_apps) + len(boxes)
        if total_refs > MAX_APP_CALL_FOREIGN_REFERENCES:
            raise ValueError(
                f"Resource reference limit of {MAX_APP_CALL_FOREIGN_REFERENCES} exceeded in transaction {i}"
            )

        # Update transaction
        app_txn.accounts = accounts
        app_txn.foreign_apps = foreign_apps
        app_txn.foreign_assets = foreign_assets
        app_txn.boxes = boxes

    def populate_group_resource(
        txns: list[TransactionWithSigner], reference: str | BoxReference | dict[str, Any] | int, ref_type: str
    ) -> None:
        """Helper function to populate group-level resources"""

        def is_appl_below_limit(t: TransactionWithSigner) -> bool:
            if not isinstance(t.txn, transaction.ApplicationCallTxn):
                return False

            app_txn = t.txn
            accounts = len(app_txn.accounts or [])
            assets = len(app_txn.foreign_assets or [])
            apps = len(app_txn.foreign_apps or [])
            boxes = len(app_txn.boxes or [])

            return accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES

        # Handle asset holding and app local references
        if ref_type in ("assetHolding", "appLocal"):
            ref_dict = cast(dict[str, Any], reference)
            account = ref_dict["account"]

            # Try to find transaction with account already available
            txn_idx = next(
                (
                    i
                    for i, t in enumerate(txns)
                    if is_appl_below_limit(t)
                    and isinstance(t.txn, transaction.ApplicationCallTxn)
                    and (
                        account in (getattr(t.txn, "accounts", []) or [])
                        or account
                        in (
                            logic.get_application_address(app_id)
                            for app_id in (getattr(t.txn, "foreign_apps", []) or [])
                        )
                        or any(account in str(v) for v in t.txn.__dict__.values())
                    )
                ),
                -1,
            )

            if txn_idx >= 0:
                app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)
                if ref_type == "assetHolding":
                    asset_id = ref_dict["asset"]
                    app_txn.foreign_assets = [*list(getattr(app_txn, "foreign_assets", []) or []), asset_id]
                else:
                    app_id = ref_dict["app"]
                    app_txn.foreign_apps = [*list(getattr(app_txn, "foreign_apps", []) or []), app_id]
                return

        # Find available transaction for the resource
        txn_idx = next(
            (
                i
                for i, t in enumerate(txns)
                if is_appl_below_limit(t)
                and isinstance(t.txn, transaction.ApplicationCallTxn)
                and (
                    len(getattr(t.txn, "accounts", []) or []) < MAX_APP_CALL_ACCOUNT_REFERENCES
                    if ref_type == "account"
                    else True
                )
            ),
            -1,
        )

        if txn_idx == -1:
            raise ValueError("No more transactions below reference limit. Add another app call to the group.")

        app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)

        # Add resource based on type
        if ref_type == "account":
            accounts = list(getattr(app_txn, "accounts", []) or [])
            accounts.append(cast(str, reference))
            app_txn.accounts = accounts
        elif ref_type == "app":
            foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
            foreign_apps.append(int(cast(str | int, reference)))
            app_txn.foreign_apps = foreign_apps
        elif ref_type == "box":
            box_ref = cast(BoxReference, reference)
            boxes = list(getattr(app_txn, "boxes", []) or [])
            boxes.append(box_ref)
            app_txn.boxes = boxes
            if box_ref.app_index != 0:
                foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
                foreign_apps.append(box_ref.app_index)
                app_txn.foreign_apps = foreign_apps
        elif ref_type == "asset":
            foreign_assets = list(getattr(app_txn, "foreign_assets", []) or [])
            foreign_assets.append(int(cast(str | int, reference)))
            app_txn.foreign_assets = foreign_assets
        elif ref_type == "assetHolding":
            ref_dict = cast(dict[str, Any], reference)
            foreign_assets = list(getattr(app_txn, "foreign_assets", []) or [])
            foreign_assets.append(ref_dict["asset"])
            app_txn.foreign_assets = foreign_assets
            accounts = list(getattr(app_txn, "accounts", []) or [])
            accounts.append(ref_dict["account"])
            app_txn.accounts = accounts
        elif ref_type == "appLocal":
            ref_dict = cast(dict[str, Any], reference)
            foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
            foreign_apps.append(ref_dict["app"])
            app_txn.foreign_apps = foreign_apps
            accounts = list(getattr(app_txn, "accounts", []) or [])
            accounts.append(ref_dict["account"])
            app_txn.accounts = accounts

    # Process group-level resources
    group_resources = unnamed_resources["group"]
    if group_resources:
        # Handle cross-reference resources first
        for app_local in group_resources.get("appLocals", []):
            populate_group_resource(group, app_local, "appLocal")
            # Remove processed resources
            if "accounts" in group_resources:
                group_resources["accounts"] = [
                    acc for acc in group_resources["accounts"] if acc != app_local["account"]
                ]
            if "apps" in group_resources:
                group_resources["apps"] = [app for app in group_resources["apps"] if int(app) != int(app_local["app"])]

        for asset_holding in group_resources.get("assetHoldings", []):
            populate_group_resource(group, asset_holding, "assetHolding")
            # Remove processed resources
            if "accounts" in group_resources:
                group_resources["accounts"] = [
                    acc for acc in group_resources["accounts"] if acc != asset_holding["account"]
                ]
            if "assets" in group_resources:
                group_resources["assets"] = [
                    asset for asset in group_resources["assets"] if int(asset) != int(asset_holding["asset"])
                ]

        # Handle remaining resources
        for account in group_resources.get("accounts", []):
            populate_group_resource(group, account, "account")

        for box in group_resources.get("boxes", []):
            populate_group_resource(group, box, "box")
            if "apps" in group_resources:
                group_resources["apps"] = [app for app in group_resources["apps"] if int(app) != int(box.app_index)]

        for asset in group_resources.get("assets", []):
            populate_group_resource(group, asset, "asset")

        for app in group_resources.get("apps", []):
            populate_group_resource(group, app, "app")

        # Handle extra box references
        extra_box_refs = group_resources.get("extraBoxRefs", 0)
        for _ in range(extra_box_refs):
            empty_box = BoxReference(0, b"")
            populate_group_resource(group, empty_box, "box")

    # Create new ATC with updated transactions
    new_atc = AtomicTransactionComposer()
    for txn_with_signer in group:
        txn_with_signer.txn.group = None
        new_atc.add_transaction(txn_with_signer)

    # Copy method calls
    new_atc.method_dict = atc.method_dict.copy()

    return new_atc


def get_unnamed_app_call_resources_accessed(atc: AtomicTransactionComposer, algod: AlgodClient) -> dict[str, Any]:
    """Get unnamed resources accessed by application calls in an atomic transaction group."""
    # Create simulation request with required flags
    simulate_request = SimulateRequest(
        txn_groups=[], allow_unnamed_resources=True, allow_empty_signatures=True, extra_opcode_budget=0
    )

    # Create empty signer
    null_signer = EmptySigner()

    # Clone the ATC and replace signers
    empty_signer_atc = atc.clone()
    for txn in empty_signer_atc.txn_list:
        txn.signer = null_signer

    # Run simulation
    result = empty_signer_atc.simulate(algod, simulate_request)

    # Get first group response
    group_response = result.simulate_response["txn-groups"][0]

    # Check for simulation failure
    if group_response.get("failure-message"):
        failed_at = group_response.get("failed-at", [0])[0]
        raise AtomicTransactionComposerError(
            f"Error during resource population simulation in transaction {failed_at}: "
            f"{group_response['failure-message']}"
        )

    # Return resources accessed at group and transaction level
    return {
        "group": group_response.get("unnamed-resources-accessed", {}),
        "txns": [txn.get("unnamed-resources-accessed", {}) for txn in group_response.get("txn-results", [])],
    }
