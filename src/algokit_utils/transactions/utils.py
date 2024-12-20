import base64
from copy import deepcopy
from typing import Any, cast

from algosdk import logic, transaction
from algosdk.atomic_transaction_composer import AtomicTransactionComposer, EmptySigner, TransactionWithSigner
from algosdk.error import AtomicTransactionComposerError
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup

from algokit_utils.models.state import BoxReference

__all__ = [
    "get_unnamed_app_call_resources_accessed",
    "populate_app_call_resources",
]

# Constants
MAX_APP_CALL_ACCOUNT_REFERENCES = 4
MAX_APP_CALL_FOREIGN_REFERENCES = 8


def _find_available_transaction_index(
    txns: list[TransactionWithSigner], reference_type: str, reference: str | dict[str, Any] | int
) -> int:
    """Find index of first transaction that can accommodate the new reference."""

    def check_transaction(txn: TransactionWithSigner) -> bool:
        # Skip if not an application call transaction
        if txn.txn.type != "appl":
            return False

        # Get current counts (using get() with default 0 for Pythonic null handling)
        accounts = len(getattr(txn.txn, "accounts", []) or [])
        assets = len(getattr(txn.txn, "foreign_assets", []) or [])
        apps = len(getattr(txn.txn, "foreign_apps", []) or [])
        boxes = len(getattr(txn.txn, "boxes", []) or [])

        # For account references, only check account limit
        if reference_type == "account":
            return accounts < MAX_APP_CALL_ACCOUNT_REFERENCES

        # For asset holdings or local state, need space for both account and other reference
        if reference_type in ("asset_holding", "app_local"):
            return (
                accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES - 1
                and accounts < MAX_APP_CALL_ACCOUNT_REFERENCES
            )

        # For boxes with non-zero app ID, need space for box and app reference
        if reference_type == "box" and reference and int(getattr(reference, "app", 0)) != 0:
            return accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES - 1

        # Default case - just check total references
        return accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES

    # Return first matching index or -1 if none found
    return next((i for i, txn in enumerate(txns) if check_transaction(txn)), -1)


def populate_app_call_resources(atc: AtomicTransactionComposer, algod: AlgodClient) -> AtomicTransactionComposer:  # noqa: C901, PLR0915, PLR0912
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
        if txn_resources.get("boxes") or txn_resources.get("extra-box-refs"):
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

    def populate_group_resource(  # noqa: C901, PLR0912, PLR0915
        txns: list[TransactionWithSigner], reference: str | dict[str, Any] | int, ref_type: str
    ) -> None:
        """Helper function to populate group-level resources matching TypeScript implementation"""

        def is_appl_below_limit(t: TransactionWithSigner) -> bool:
            if not isinstance(t.txn, transaction.ApplicationCallTxn):
                return False

            accounts = len(getattr(t.txn, "accounts", []) or [])
            assets = len(getattr(t.txn, "foreign_assets", []) or [])
            apps = len(getattr(t.txn, "foreign_apps", []) or [])
            boxes = len(getattr(t.txn, "boxes", []) or [])

            return accounts + assets + apps + boxes < MAX_APP_CALL_FOREIGN_REFERENCES

        # Handle asset holding and app local references first
        if ref_type in ("assetHolding", "appLocal"):
            ref_dict = cast(dict[str, Any], reference)
            account = ref_dict["account"]

            # First try to find transaction with account already available
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
                        or any(str(account) in str(v) for v in t.txn.__dict__.values())
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

            # Try to find transaction that already has the app/asset available
            txn_idx = next(
                (
                    i
                    for i, t in enumerate(txns)
                    if is_appl_below_limit(t)
                    and isinstance(t.txn, transaction.ApplicationCallTxn)
                    and len(getattr(t.txn, "accounts", []) or []) < MAX_APP_CALL_ACCOUNT_REFERENCES
                    and (
                        (
                            ref_type == "assetHolding"
                            and ref_dict["asset"] in (getattr(t.txn, "foreign_assets", []) or [])
                        )
                        or (
                            ref_type == "appLocal"
                            and (
                                ref_dict["app"] in (getattr(t.txn, "foreign_apps", []) or [])
                                or t.txn.index == ref_dict["app"]
                            )
                        )
                    )
                ),
                -1,
            )

            if txn_idx >= 0:
                app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)
                accounts = list(getattr(app_txn, "accounts", []) or [])
                accounts.append(account)
                app_txn.accounts = accounts
                return

        # Handle box references
        if ref_type == "box":
            box_ref: tuple[int, bytes] = (reference["app"], base64.b64decode(reference["name"]))  # type: ignore  # noqa: PGH003

            # Try to find transaction that already has the app available
            txn_idx = next(
                (
                    i
                    for i, t in enumerate(txns)
                    if is_appl_below_limit(t)
                    and isinstance(t.txn, transaction.ApplicationCallTxn)
                    and (box_ref[0] in (getattr(t.txn, "foreign_apps", []) or []) or t.txn.index == box_ref[0])
                ),
                -1,
            )

            if txn_idx >= 0:
                app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)
                boxes = list(getattr(app_txn, "boxes", []) or [])
                boxes.append(BoxReference.translate_box_reference(box_ref, app_txn.foreign_apps or [], app_txn.index))
                app_txn.boxes = boxes
                return

        # Find available transaction for the resource
        txn_idx = _find_available_transaction_index(txns, ref_type, reference)

        if txn_idx == -1:
            raise ValueError("No more transactions below reference limit. Add another app call to the group.")

        app_txn = cast(transaction.ApplicationCallTxn, txns[txn_idx].txn)

        if ref_type == "account":
            accounts = list(getattr(app_txn, "accounts", []) or [])
            accounts.append(cast(str, reference))
            app_txn.accounts = accounts
        elif ref_type == "app":
            app_id = int(cast(str | int, reference))
            foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
            foreign_apps.append(app_id)
            app_txn.foreign_apps = foreign_apps
        elif ref_type == "box":
            boxes = list(getattr(app_txn, "boxes", []) or [])
            boxes.append(BoxReference.translate_box_reference(box_ref, app_txn.foreign_apps or [], app_txn.index))
            app_txn.boxes = boxes
            if box_ref[0] != 0:
                foreign_apps = list(getattr(app_txn, "foreign_apps", []) or [])
                foreign_apps.append(box_ref[0])
                app_txn.foreign_apps = foreign_apps
        elif ref_type == "asset":
            asset_id = int(cast(str | int, reference))
            foreign_assets = list(getattr(app_txn, "foreign_assets", []) or [])
            foreign_assets.append(asset_id)
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
        extra_box_refs = group_resources.get("extra-box-refs", 0)
        for _ in range(extra_box_refs):
            populate_group_resource(group, {"app": 0, "name": ""}, "box")

    # Create new ATC with updated transactions
    new_atc = AtomicTransactionComposer()
    for txn_with_signer in group:
        txn_with_signer.txn.group = None
        new_atc.add_transaction(txn_with_signer)

    # Copy method calls
    new_atc.method_dict = deepcopy(atc.method_dict)

    return new_atc


def get_unnamed_app_call_resources_accessed(atc: AtomicTransactionComposer, algod: AlgodClient) -> dict[str, Any]:
    """Get unnamed resources accessed by application calls in an atomic transaction group."""
    # Create simulation request with required flags
    simulate_request = SimulateRequest(txn_groups=[], allow_unnamed_resources=True, allow_empty_signatures=True)

    # Create empty signer
    null_signer = EmptySigner()

    # Clone the ATC and replace signers
    unsigned_txn_groups = atc.build_group()
    txn_group = [
        SimulateRequestTransactionGroup(
            txns=null_signer.sign_transactions([txn_group.txn for txn_group in unsigned_txn_groups], [])
        )
    ]
    simulate_request = SimulateRequest(txn_groups=txn_group, allow_unnamed_resources=True, allow_empty_signatures=True)

    # Run simulation
    result = atc.simulate(algod, simulate_request)

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


MAX_LEASE_LENGTH = 32


def encode_lease(lease: str | bytes | None) -> bytes | None:
    if lease is None:
        return None
    elif isinstance(lease, bytes):
        if not (1 <= len(lease) <= MAX_LEASE_LENGTH):
            raise ValueError(
                f"Received invalid lease; expected something with length between 1 and {MAX_LEASE_LENGTH}, "
                f"but received bytes with length {len(lease)}"
            )
        if len(lease) == MAX_LEASE_LENGTH:
            return lease
        lease32 = bytearray(32)
        lease32[: len(lease)] = lease
        return bytes(lease32)
    elif isinstance(lease, str):
        encoded = lease.encode("utf-8")
        if not (1 <= len(encoded) <= MAX_LEASE_LENGTH):
            raise ValueError(
                f"Received invalid lease; expected something with length between 1 and {MAX_LEASE_LENGTH}, "
                f"but received '{lease}' with length {len(lease)}"
            )
        lease32 = bytearray(MAX_LEASE_LENGTH)
        lease32[: len(encoded)] = encoded
        return bytes(lease32)
    else:
        raise TypeError(f"Unknown lease type received of {type(lease)}")
