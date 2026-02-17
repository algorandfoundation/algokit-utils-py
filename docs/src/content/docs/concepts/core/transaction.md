---
title: "Transaction management"
description: "Transaction management is one of the core capabilities provided by AlgoKit Utils. It allows you to construct, simulate and send single, or grouped transactions with consistent and highly configurable semantics."
---

Transaction management is one of the core capabilities provided by AlgoKit Utils. It allows you to construct, simulate and send single, or grouped transactions with consistent and highly configurable semantics, including configurable control of transaction notes, logging, fees, multiple sender account types, and sending behaviour.

## SendSingleTransactionResult

All AlgoKit Utils functions that send a transaction will generally return a variant of the `SendSingleTransactionResult` dataclass or some superset of that. This provides a consistent mechanism to interpret the results of a transaction send.

It consists of the following properties:

- `transaction`: A `Transaction` object that represents the last transaction that was sent
- `confirmation`: A `PendingTransactionResponse` object, which is a type-safe wrapper of the return from the algod pending transaction API noting that it will only be returned if the transaction was able to be confirmed (so won't represent a "pending" transaction)
- `tx_id`: The transaction ID of the last transaction (`str | None`)
- `group_id`: The group ID of the transaction group (`str`)
- `tx_ids`: The full array of transaction IDs (`list[str]`)
- `transactions`: The full array of transactions (`list[Transaction]`)
- `confirmations`: The full array of confirmations (`list[PendingTransactionResponse]`)
- `returns`: The ABI return values if applicable (`list[ABIReturn] | None`)

There are various variations of `SendSingleTransactionResult` that are exposed by various functions within AlgoKit Utils, including:

- `SendSingleAssetCreateTransactionResult` - Extends the base result with `asset_id` for newly created ASAs
- `SendAppTransactionResult` - Result from calling a single app call, adds `abi_return` for ABI method return values
- `SendAppUpdateTransactionResult` - Extends `SendAppTransactionResult` with `compiled_approval` and `compiled_clear` programs
- `SendAppCreateTransactionResult` - Extends `SendAppUpdateTransactionResult` with `app_id` and `app_address` of the newly created application
- `SendTransactionComposerResults` - The result from sending the transactions within a `TransactionComposer`, with `tx_ids`, `transactions`, `confirmations`, `returns`, `group_id`, and optional `simulate_response`
- `SendAppFactoryTransactionResult` / `SendAppCreateFactoryTransactionResult` / `SendAppUpdateFactoryTransactionResult` - Factory-level results where `abi_return` is the already-parsed ARC-56 return value (typed as `Arc56ReturnValueType`) rather than the raw `ABIReturn` object

## Further reading

To understand how to create, simulate and send transactions consult the [`AlgorandClient`](../algorand-client) and [`TransactionComposer`](../../advanced/transaction-composer) documentation.
