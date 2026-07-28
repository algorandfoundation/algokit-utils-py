---
title: "Asset management"
description: "How to create, opt into, transfer, freeze, clawback, and destroy Algorand Standard Assets with AlgoKit Utils Python."
---

import RemoteCode from "/src/components/RemoteCode.astro";

<!-- TODO: src points at `docs-staging` because that is the only pushed branch
containing examples/concepts/assets.py. examples/README.md specifies the `main`
URL as the final form: switch every src to
https://raw.githubusercontent.com/algorandfoundation/algokit-utils-py/main/examples/concepts/assets.py
once this work has merged to main. -->

This page shows how to perform each Algorand Standard Asset (ASA) operation with AlgoKit Utils Python. For the protocol-level view of what an ASA is and how its control roles, holdings, opt-in requirement, freezing, clawback, and destruction behave, see the main DevPortal [Assets overview](/concepts/assets/overview/) and [Asset Operations](/concepts/assets/asset-operations/) pages.

Each operation is invoked through `algorand.send.<operation>(params)`, where `params` is a typed parameter object such as `AssetCreateParams` or `AssetTransferParams`. To build an unsigned transaction instead of sending, use `algorand.create_transaction.<operation>(params)`. To add the operation to an atomic transaction group, use `algorand.new_group().add_<operation>(params)`. See [`AlgorandClient`](/docs/algokit-utils/python/latest/concepts/core/algorand-client/) for how these dispatch surfaces relate.

:::note[Editor's note]
Once [Guides > Assets](/docs/algokit-utils/python/latest/guides/assets/) is published, replace this with: "For end-to-end examples, see the [Assets guide](/docs/algokit-utils/python/latest/guides/assets/)."
:::

## Create an Asset

Creating an ASA mints a new token on the Algorand blockchain. Any account with a sufficient Algo balance can create an asset, and the sender becomes the asset's creator. Sending an asset-create transaction returns the newly assigned asset ID.

<RemoteCode
  src="https://raw.githubusercontent.com/algorandfoundation/algokit-utils-py/docs-staging/examples/concepts/assets.py"
  snippet="CREATE_ASSET"
  lang="python"
/>

## Opting In and Out of Assets

An account must opt in to an ASA before it can hold or receive units of that asset, and can opt out to release the associated minimum balance requirement. The library exposes individual and bulk variants for both directions.

### Opt In

Opting in increases the account's minimum balance requirement by 0.1 Algo per asset.

<RemoteCode
  src="https://raw.githubusercontent.com/algorandfoundation/algokit-utils-py/docs-staging/examples/concepts/assets.py"
  snippet="OPT_IN_ASSET"
  lang="python"
/>

### Bulk Opt In

`algorand.asset.bulk_opt_in(...)` opts an account into a list of assets in one call by sending the opt-in transactions as an atomic group. It applies when a single account needs to receive several assets at once.

<!-- TODO: no BULK_OPT_IN_ASSET snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: BULK_OPT_IN_ASSET` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

### Opt Out

Opting out releases the 0.1 Algo minimum balance requirement associated with holding the asset. The receiver of any remaining balance is specified in the params. By default, `algorand.send.asset_opt_out` verifies a zero balance before submission (`ensure_zero_balance=True`) to prevent asset loss. See [Safety Considerations](#safety-considerations).

<!-- TODO: no OPT_OUT_ASSET snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: OPT_OUT_ASSET` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

### Bulk Opt Out

`algorand.asset.bulk_opt_out(...)` opts an account out of a list of assets in a single call. It provides the same zero-balance protection as `algorand.send.asset_opt_out` by default. See [Safety Considerations](#safety-considerations).

<!-- TODO: no BULK_OPT_OUT_ASSET snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: BULK_OPT_OUT_ASSET` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

## Transfer an Asset

Asset transfers move units of an ASA between accounts that have both opted in. The sender must hold at least the transferred amount and must be authorized to send the asset.

<RemoteCode
  src="https://raw.githubusercontent.com/algorandfoundation/algokit-utils-py/docs-staging/examples/concepts/assets.py"
  snippet="TRANSFER_ASSET"
  lang="python"
/>

## Access Control

The operations in this section update or exercise an asset's authority roles: `manager`, `reserve`, `freeze`, and `clawback`. Each requires the corresponding authority as the transaction sender.

### Reconfigure an Asset

Reconfiguration updates the mutable control addresses of an asset: `manager`, `reserve`, `freeze`, and `clawback`. The current manager account must send the transaction. A control-address field left unset on `AssetConfigParams` is cleared permanently by the protocol at submission. See [Safety Considerations](#safety-considerations).

<!-- TODO: no RECONFIGURE_ASSET snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: RECONFIGURE_ASSET` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

### Freeze or Unfreeze Assets

A freeze transaction toggles whether a specified account can move a specific asset. The `frozen` flag on `AssetFreezeParams` controls whether the holding is frozen or unfrozen. The transaction must be signed by the asset's freeze authority.

<!-- TODO: no FREEZE_ASSET snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: FREEZE_ASSET` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

### Clawback Assets

A clawback moves an asset holding out of another account without that holder's consent. It is expressed as an `AssetTransferParams` with `clawback_target` set to the account the assets are pulled from. The sender must be the asset's clawback authority. There is no dedicated clawback parameter type. See [Safety Considerations](#safety-considerations).

<!-- TODO: no CLAWBACK_ASSET snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: CLAWBACK_ASSET` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

## Destroy an Asset

Destroying an asset permanently removes it from the blockchain and releases the creator's minimum balance requirement for it. Destruction requires that the current manager sign the transaction and that all units of the asset sit in the creator account.

<!-- TODO: no DESTROY_ASSET snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: DESTROY_ASSET` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

## Asset Queries

`algorand.asset` exposes an [`AssetManager`](/docs/algokit-utils/python/latest/api/algokit_utils/assets/asset_manager/) for asset queries and higher-level bulk helpers. The bulk helpers (`bulk_opt_in`, `bulk_opt_out`) are covered in the sections above. Two query methods remain:

- `algorand.asset.get_by_id(asset_id)` returns the asset's parameters (total supply, decimals, unit name, control addresses, and so on).
- `algorand.asset.get_account_information(sender, asset_id)` returns the given account's holding for the asset.

For any individual asset transaction not covered by a bulk helper, use the standard dispatch surfaces (`algorand.send`, `algorand.create_transaction`, or `algorand.new_group()`) with the typed parameter objects shown above.

<!-- TODO: no ASSET_MANAGER_QUERIES snippet exists in examples/concepts/assets.py on
docs-staging yet. Add a `# example: ASSET_MANAGER_QUERIES` region to that script, then
render it here with a RemoteCode block matching the ones above. -->

## Safety Considerations

A few asset behaviors deserve attention because their effects are hard or impossible to reverse. The [main DevPortal Asset Operations](/concepts/assets/asset-operations/) page describes the protocol-level rules in full; the notes below focus on library-level behavior.

- **Reconfiguration can permanently clear control addresses.** A control-address field left unset on `AssetConfigParams` is cleared permanently by the protocol at submission. A partial reconfiguration that omits a role removes that role from the asset for the remainder of its lifetime.
- **Clawback removes assets from another account without the holder's consent.** A clawback is a transfer signed by the clawback authority, which can move assets out of any opted-in account without further approval from the holder.
- **Opting out with a remaining balance can result in losing those assets.** Both `algorand.send.asset_opt_out` and `algorand.asset.bulk_opt_out` verify a zero balance before submission by default (`ensure_zero_balance=True`). With that check disabled, the opt-out proceeds even when the account still holds units of the asset, and those units are forfeited on submission.
- **Freeze and unfreeze require the freeze authority as sender.** A freeze transaction signed by any other account is invalid at the protocol level.
- **Reconfiguration requires the manager as sender.** If the manager role has been cleared, no further reconfiguration is possible.
- **Destruction requires the manager and full creator ownership.** All units must sit in the creator account, and the sender must be the current manager.

## Related Documentation

- Main DevPortal: [Assets overview](/concepts/assets/overview/), [Asset Operations](/concepts/assets/asset-operations/), [Asset Metadata](/concepts/assets/asset-metadata/)
- AlgoKit Utils Python: [Algorand Client](/docs/algokit-utils/python/latest/concepts/core/algorand-client/), [Transaction](/docs/algokit-utils/python/latest/concepts/core/transaction/), [Transaction Composer](/docs/algokit-utils/python/latest/concepts/advanced/transaction-composer/), [Assets guide](/docs/algokit-utils/python/latest/concepts/building/asset/)
- API Reference: [Asset transaction types](/docs/algokit-utils/python/latest/api/algokit_utils/transactions/types/), [`AssetManager` reference](/docs/algokit-utils/python/latest/api/algokit_utils/assets/asset_manager/), [Transactions overview](/docs/algokit-utils/python/latest/api/algokit_utils/transactions/)
- Examples: [Transact asset examples](/docs/algokit-utils/python/latest/examples/transact/), [Algorand Client asset examples](/docs/algokit-utils/python/latest/examples/algorand-client/)
