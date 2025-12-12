from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from algokit_algod_client import models as algod_models
from algokit_common import get_application_address
from algokit_common.constants import MAX_ACCOUNT_REFERENCES, MAX_OVERALL_REFERENCES
from algokit_transact.models.app_call import AppCallTransactionFields, BoxReference
from algokit_transact.models.transaction import Transaction, TransactionType


def populate_transaction_resources(  # noqa: C901, PLR0912
    transaction: Transaction,
    resources_accessed: algod_models.SimulateUnnamedResourcesAccessed,
    group_index: int,
) -> Transaction:
    """
    Populate transaction-level resources for app call transactions
    """
    if transaction.transaction_type != TransactionType.AppCall or transaction.application_call is None:
        return transaction

    # Check for unexpected resources at transaction level
    if resources_accessed.boxes or resources_accessed.extra_box_refs:
        raise ValueError("Unexpected boxes at the transaction level")
    if resources_accessed.app_locals:
        raise ValueError("Unexpected app locals at the transaction level")
    if resources_accessed.asset_holdings:
        raise ValueError("Unexpected asset holdings at the transaction level")

    app_call = transaction.application_call
    updated_app_call = app_call
    accounts_count = len(app_call.account_references or [])
    apps_count = len(app_call.app_references or [])
    assets_count = len(app_call.asset_references or [])
    boxes_count = len(app_call.box_references or [])

    # Populate accounts
    if resources_accessed.accounts:
        current_accounts = list(app_call.account_references or [])
        for account in resources_accessed.accounts:
            normalized = _normalize_address(account)
            if normalized not in current_accounts:
                current_accounts.append(normalized)
        if len(current_accounts) != accounts_count:
            updated_app_call = replace(updated_app_call, account_references=current_accounts)
            accounts_count = len(current_accounts)

    # Populate apps
    if resources_accessed.apps:
        current_apps = list(updated_app_call.app_references or [])
        for app_id in resources_accessed.apps:
            if app_id not in current_apps:
                current_apps.append(app_id)
        if len(current_apps) != apps_count:
            updated_app_call = replace(updated_app_call, app_references=current_apps)
            apps_count = len(current_apps)

    # Populate assets
    if resources_accessed.assets:
        current_assets = list(updated_app_call.asset_references or [])
        for asset_id in resources_accessed.assets:
            if asset_id not in current_assets:
                current_assets.append(asset_id)
        if len(current_assets) != assets_count:
            updated_app_call = replace(updated_app_call, asset_references=current_assets)
            assets_count = len(current_assets)

    # Validate reference limits
    if accounts_count + assets_count + apps_count + boxes_count > MAX_OVERALL_REFERENCES:
        raise ValueError(f"Resource reference limit of {MAX_OVERALL_REFERENCES} exceeded in transaction {group_index}")

    if updated_app_call is app_call:
        return transaction
    return replace(transaction, application_call=updated_app_call)


class GroupResourceType(Enum):
    """Describes different group resources"""

    Account = "Account"
    App = "App"
    Asset = "Asset"
    Box = "Box"
    ExtraBoxRef = "ExtraBoxRef"
    AssetHolding = "AssetHolding"
    AppLocal = "AppLocal"


@dataclass(slots=True)
class GroupResourceToPopulate:
    type: GroupResourceType
    data: Any


def populate_group_resources(  # noqa: C901, PLR0912
    transactions: list[Transaction],
    group_resources: algod_models.SimulateUnnamedResourcesAccessed,
) -> None:
    """
    Populate group-level resources for app call transactions
    """
    remaining_accounts = list(group_resources.accounts or [])
    remaining_apps = list(group_resources.apps or [])
    remaining_assets = list(group_resources.assets or [])
    remaining_boxes = list(group_resources.boxes or [])

    # Process cross-reference resources first (app locals and asset holdings) as they are most restrictive
    if group_resources.app_locals:
        for app_local in group_resources.app_locals:
            _populate_group_resource(transactions, GroupResourceToPopulate(GroupResourceType.AppLocal, app_local))
            # Remove resources from remaining if we're adding them here
            if app_local.address in remaining_accounts:
                remaining_accounts.remove(app_local.address)
            if app_local.app_id in remaining_apps:
                remaining_apps.remove(app_local.app_id)

    if group_resources.asset_holdings:
        for asset_holding in group_resources.asset_holdings:
            _populate_group_resource(
                transactions, GroupResourceToPopulate(GroupResourceType.AssetHolding, asset_holding)
            )
            # Remove resources from remaining if we're adding them here
            if asset_holding.address in remaining_accounts:
                remaining_accounts.remove(asset_holding.address)
            if asset_holding.asset_id in remaining_assets:
                remaining_assets.remove(asset_holding.asset_id)

    # Process accounts next
    for account in remaining_accounts:
        _populate_group_resource(transactions, GroupResourceToPopulate(GroupResourceType.Account, account))

    # Process boxes
    for box_ref in remaining_boxes:
        _populate_group_resource(
            transactions,
            GroupResourceToPopulate(
                GroupResourceType.Box,
                BoxReference(app_id=box_ref.app_id, name=box_ref.name),
            ),
        )
        # Remove apps as resource if we're adding it here
        if box_ref.app_id in remaining_apps:
            remaining_apps.remove(box_ref.app_id)

    # Process assets
    for asset in remaining_assets:
        _populate_group_resource(transactions, GroupResourceToPopulate(GroupResourceType.Asset, asset))

    # Process remaining apps
    for app in remaining_apps:
        _populate_group_resource(transactions, GroupResourceToPopulate(GroupResourceType.App, app))

    # Handle extra box refs
    if group_resources.extra_box_refs:
        for _ in range(group_resources.extra_box_refs):
            _populate_group_resource(transactions, GroupResourceToPopulate(GroupResourceType.ExtraBoxRef, None))


def _is_app_call_below_resource_limit(txn: Transaction) -> bool:
    if txn.transaction_type != TransactionType.AppCall or txn.application_call is None:
        return False
    if txn.application_call.access_references:
        return False

    accounts_count = len(txn.application_call.account_references or [])
    assets_count = len(txn.application_call.asset_references or [])
    apps_count = len(txn.application_call.app_references or [])
    boxes_count = len(txn.application_call.box_references or [])

    return accounts_count + assets_count + apps_count + boxes_count < MAX_OVERALL_REFERENCES


def _get_app_address(app_id: int) -> str:
    return get_application_address(app_id)


def _populate_group_resource(  # noqa: C901, PLR0912, PLR0915
    transactions: list[Transaction],
    resource: GroupResourceToPopulate,
) -> None:
    # For asset holdings and app locals, first try to find a transaction that already has the account available
    if resource.type in (GroupResourceType.AssetHolding, GroupResourceType.AppLocal):
        account = _normalize_address(resource.data.address)

        # Try to find a transaction that already has the account available
        group_index1 = -1
        for i, txn in enumerate(transactions):
            if not _is_app_call_below_resource_limit(txn):
                continue

            app_call = txn.application_call
            assert app_call is not None

            # Check if account is in foreign accounts array
            if app_call.account_references and account in app_call.account_references:
                group_index1 = i
                break

            # Check if account is available as an app account
            if app_call.app_references:
                found = False
                for app_id in app_call.app_references:
                    if account == _get_app_address(app_id):
                        found = True
                        break
                if found:
                    group_index1 = i
                    break

            # Check if account appears in any app call transaction fields
            if txn.sender == account:
                group_index1 = i
                break

        if group_index1 != -1:
            app_call = transactions[group_index1].application_call
            assert app_call is not None
            if resource.type == GroupResourceType.AssetHolding:
                current_assets = list(app_call.asset_references or [])
                if resource.data.asset_id not in current_assets:
                    current_assets.append(resource.data.asset_id)
                app_call = replace(app_call, asset_references=current_assets)
                _set_app_call(transactions, group_index1, app_call)
            else:
                current_apps = list(app_call.app_references or [])
                if resource.data.app_id not in current_apps:
                    current_apps.append(resource.data.app_id)
                app_call = replace(app_call, app_references=current_apps)
                _set_app_call(transactions, group_index1, app_call)
            return

        # Try to find a transaction that has the asset/app available and space for account
        group_index2 = -1
        for i, txn in enumerate(transactions):
            if not _is_app_call_below_resource_limit(txn):
                continue

            app_call = txn.application_call
            assert app_call is not None
            if len(app_call.account_references or []) >= MAX_ACCOUNT_REFERENCES:
                continue

            if resource.type == GroupResourceType.AssetHolding:
                if app_call.asset_references and resource.data.asset_id in app_call.asset_references:
                    group_index2 = i
                    break
            elif (
                app_call.app_references and resource.data.app_id in app_call.app_references
            ) or app_call.app_id == resource.data.app_id:
                group_index2 = i
                break

        if group_index2 != -1:
            app_call = transactions[group_index2].application_call
            assert app_call is not None
            current_accounts = list(app_call.account_references or [])
            if account not in current_accounts:
                current_accounts.append(account)
            app_call = replace(app_call, account_references=current_accounts)
            _set_app_call(transactions, group_index2, app_call)
            return

    # For boxes, first try to find a transaction that already has the app available
    if resource.type == GroupResourceType.Box:
        group_index = -1
        for i, txn in enumerate(transactions):
            if not _is_app_call_below_resource_limit(txn):
                continue

            app_call = txn.application_call
            assert app_call is not None
            if (
                app_call.app_references and resource.data.app_id in app_call.app_references
            ) or app_call.app_id == resource.data.app_id:
                group_index = i
                break

        if group_index != -1:
            app_call = transactions[group_index].application_call
            assert app_call is not None
            current_boxes = list(app_call.box_references or [])
            exists = any(b.app_id == resource.data.app_id and b.name == resource.data.name for b in current_boxes)
            if not exists:
                current_boxes.append(BoxReference(app_id=resource.data.app_id, name=resource.data.name))
            app_call = replace(app_call, box_references=current_boxes)
            _set_app_call(transactions, group_index, app_call)
            return

    # Find the first transaction that can accommodate the resource
    group_index = -1
    for i, txn in enumerate(transactions):
        if txn.transaction_type != TransactionType.AppCall or txn.application_call is None:
            continue
        if txn.application_call.access_references:
            continue

        app_call = txn.application_call
        accounts_count = len(app_call.account_references or [])
        assets_count = len(app_call.asset_references or [])
        apps_count = len(app_call.app_references or [])
        boxes_count = len(app_call.box_references or [])

        if resource.type == GroupResourceType.Account:
            if accounts_count + assets_count + apps_count + boxes_count < MAX_OVERALL_REFERENCES:
                group_index = i
                break
        elif resource.type in (GroupResourceType.AssetHolding, GroupResourceType.AppLocal):
            if accounts_count + assets_count + apps_count + boxes_count < MAX_OVERALL_REFERENCES - 1:
                group_index = i
                break
        elif resource.type == GroupResourceType.Box:
            if resource.data.app_id != 0:
                if accounts_count + assets_count + apps_count + boxes_count < MAX_OVERALL_REFERENCES - 1:
                    group_index = i
                    break
            elif accounts_count + assets_count + apps_count + boxes_count < MAX_OVERALL_REFERENCES:
                group_index = i
                break
        elif accounts_count + assets_count + apps_count + boxes_count < MAX_OVERALL_REFERENCES:
            group_index = i
            break

    if group_index == -1:
        raise ValueError("No more transactions below reference limit. Add another app call to the group.")

    app_call = transactions[group_index].application_call
    assert app_call is not None

    if resource.type == GroupResourceType.Account:
        current_accounts = list(app_call.account_references or [])
        account = _normalize_address(resource.data)
        if account not in current_accounts:
            current_accounts.append(account)
        app_call = replace(app_call, account_references=current_accounts)
        _set_app_call(transactions, group_index, app_call)

    elif resource.type == GroupResourceType.App:
        current_apps = list(app_call.app_references or [])
        if resource.data not in current_apps:
            current_apps.append(resource.data)
        app_call = replace(app_call, app_references=current_apps)
        _set_app_call(transactions, group_index, app_call)

    elif resource.type == GroupResourceType.Box:
        current_boxes = list(app_call.box_references or [])
        exists = any(b.app_id == resource.data.app_id and b.name == resource.data.name for b in current_boxes)
        if not exists:
            current_boxes.append(BoxReference(app_id=resource.data.app_id, name=resource.data.name))
        app_call = replace(app_call, box_references=current_boxes)
        _set_app_call(transactions, group_index, app_call)

        if resource.data.app_id != 0:
            current_apps = list(app_call.app_references or [])
            if resource.data.app_id not in current_apps:
                current_apps.append(resource.data.app_id)
            app_call = replace(app_call, app_references=current_apps)
            _set_app_call(transactions, group_index, app_call)

    elif resource.type == GroupResourceType.ExtraBoxRef:
        current_boxes = list(app_call.box_references or [])
        current_boxes.append(BoxReference(app_id=0, name=b""))
        app_call = replace(app_call, box_references=current_boxes)
        _set_app_call(transactions, group_index, app_call)

    elif resource.type == GroupResourceType.AssetHolding:
        current_assets = list(app_call.asset_references or [])
        if resource.data.asset_id not in current_assets:
            current_assets.append(resource.data.asset_id)
        app_call = replace(app_call, asset_references=current_assets)
        _set_app_call(transactions, group_index, app_call)

        current_accounts = list(app_call.account_references or [])
        account = _normalize_address(resource.data.address)
        if account not in current_accounts:
            current_accounts.append(account)
        app_call = replace(app_call, account_references=current_accounts)
        _set_app_call(transactions, group_index, app_call)

    elif resource.type == GroupResourceType.AppLocal:
        current_apps = list(app_call.app_references or [])
        if resource.data.app_id not in current_apps:
            current_apps.append(resource.data.app_id)
        app_call = replace(app_call, app_references=current_apps)
        _set_app_call(transactions, group_index, app_call)

        current_accounts = list(app_call.account_references or [])
        account = _normalize_address(resource.data.address)
        if account not in current_accounts:
            current_accounts.append(account)
        app_call = replace(app_call, account_references=current_accounts)
        _set_app_call(transactions, group_index, app_call)

    elif resource.type == GroupResourceType.Asset:
        current_assets = list(app_call.asset_references or [])
        if resource.data not in current_assets:
            current_assets.append(resource.data)
        app_call = replace(app_call, asset_references=current_assets)
        _set_app_call(transactions, group_index, app_call)


def _set_app_call(transactions: list[Transaction], index: int, app_call: AppCallTransactionFields) -> None:
    transactions[index] = replace(transactions[index], application_call=app_call)


def _normalize_address(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
