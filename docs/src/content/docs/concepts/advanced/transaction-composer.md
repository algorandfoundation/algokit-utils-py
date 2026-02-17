---
title: "Transaction composer"
description: "The `TransactionComposer` class allows you to easily compose one or more compliant Algorand transactions and execute and/or simulate them."
---

The `TransactionComposer` class allows you to easily compose one or more compliant Algorand transactions and execute and/or simulate them.

It's the core of how the [`AlgorandClient`](../../core/algorand-client) class composes and sends transactions.

To get an instance of `TransactionComposer` you can either get it from an [app client](../../building/app-client), from an [`AlgorandClient`](../../core/algorand-client), or by instantiating via the constructor.

```python
composer_from_algorand = algorand.new_group()
composer_from_app_client = app_client.algorand.new_group()
composer_from_constructor = TransactionComposer(
    TransactionComposerParams(
        algod=algod,
        # Return the TransactionSigner for this address
        get_signer=lambda address: signer,
    )
)
composer_from_constructor_with_optional_params = TransactionComposer(
    TransactionComposerParams(
        algod=algod,
        # Return the TransactionSigner for this address
        get_signer=lambda address: signer,
        get_suggested_params=lambda: algod.suggested_params(),
        default_validity_window=1000,
        app_manager=AppManager(algod),
    )
)
```

## Constructing a transaction

To construct a transaction you need to add it to the composer, passing in the relevant `params object` for that transaction. Params are Python dataclasses and all of them extend the [common call parameters](../../core/algorand-client#transaction-parameters).

The `methods to construct a transaction` are all named `add_{transaction_type}` and return an instance of the composer so they can be chained together fluently to construct a transaction group.

For example:

```python
from algokit_abi import arc56

my_method = arc56.Method.from_signature('my_method()void')
result = (
    algorand.new_group()
    .add_payment(PaymentParams(
        sender="SENDER",
        receiver="RECEIVER",
        amount=AlgoAmount.from_micro_algo(100),
    ))
    .add_app_call_method_call(AppCallMethodCallParams(
        sender="SENDER",
        app_id=123,
        method=my_method,
        args=[1, 2, 3],
    ))
)
```

## Sending a transaction

Once you have constructed all the required transactions, they can be sent by calling `send()` on the `TransactionComposer`.
Additionally `send()` takes a number of parameters which allow you to opt-in to some additional behaviours as part of sending the transaction or transaction group, most significantly `populate_app_call_resources` and `cover_app_call_inner_transaction_fees`.

### Populating App Call Resources

`populate_app_call_resources` automatically updates the relevant app call transactions in the group to include the account, app, asset and box resources required for the transactions to execute successfully. It leverages the simulate endpoint to discover the accessed resources, which have not been explicitly specified. This setting only applies when you have constructed at least one app call transaction. You can read more about [resources and the reference arrays](https://dev.algorand.co/concepts/smart-contracts/resource-usage/#what-are-reference-arrays) in the docs.

For example:

```python
from algokit_abi import arc56

my_method = arc56.Method.from_signature('my_method()void')
result = (
    algorand.new_group()
    .add_app_call_method_call(AppCallMethodCallParams(
        sender="SENDER",
        app_id=123,
        method=my_method,
        args=[1, 2, 3],
    ))
    .send(SendParams(
        populate_app_call_resources=True,
    ))
)
```

If `my_method` in the above example accesses any resources, they will be automatically discovered and added before sending the transaction to the network.

### Covering App Call Inner Transaction Fees

`cover_app_call_inner_transaction_fees` automatically calculate the required fee for a parent app call transaction that sends inner transactions. It leverages the simulate endpoint to discover the inner transactions sent and calculates a fee delta to resolve the optimal fee. This feature also takes care of accounting for any surplus transaction fee at the various levels, so as to effectively minimise the fees needed to successfully handle complex scenarios. This setting only applies when you have constructed at least one app call transaction.

For example:

```python
from algokit_abi import arc56

my_method = arc56.Method.from_signature('my_method()void')
result = (
    algorand
    .new_group()
    .add_app_call_method_call(AppCallMethodCallParams(
        sender="SENDER",
        app_id=123,
        method=my_method,
        args=[1, 2, 3],
        max_fee=AlgoAmount.from_micro_algo(5000),  # NOTE: a max_fee value is required when enabling cover_app_call_inner_transaction_fees
    ))
    .send(SendParams(cover_app_call_inner_transaction_fees=True))
)
```

Assuming the app account is not covering any of the inner transaction fees, if `my_method` in the above example sends 2 inner transactions, then the fee calculated for the parent transaction will be 3000 µALGO when the transaction is sent to the network.

The above example also has a `max_fee` of 5000 µALGO specified. An exception will be thrown if the transaction fee exceeds that value, which allows you to set fee limits. The `max_fee` field is required when enabling `cover_app_call_inner_transaction_fees`.

Because `max_fee` is required and a `Transaction` does not hold any max fee information, you cannot use the generic `add_transaction()` method on the composer with `cover_app_call_inner_transaction_fees` enabled. Instead use the below, which provides a better overall experience:

```python
my_method = arc56.Method.from_signature('my_method()void')

# Does not work
result = (
    algorand
    .new_group()
    .add_transaction(algorand.create_transaction.app_call_method_call(
        AppCallMethodCallParams(
            sender="SENDER",
            app_id=123,
            method=my_method,
            args=[1, 2, 3],
            max_fee=AlgoAmount.from_micro_algo(5000),  # This is only used to create the Transaction object and isn't made available to the composer.
        )
    ).transactions[0])
    .send(SendParams(cover_app_call_inner_transaction_fees=True))
)

# Works as expected
result = (
    algorand
    .new_group()
    .add_app_call_method_call(AppCallMethodCallParams(
        sender="SENDER",
        app_id=123,
        method=my_method,
        args=[1, 2, 3],
        max_fee=AlgoAmount.from_micro_algo(5000),
    ))
    .send(SendParams(cover_app_call_inner_transaction_fees=True))
)
```

A more complex valid scenario which leverages an app client to send an ABI method call with ABI method call transactions argument is below:

```python
app_factory = algorand.client.get_app_factory(
    app_spec="APP_SPEC",
    default_sender=sender.addr,
)

app_client_1, _ = app_factory.send.bare.create()
app_client_2, _ = app_factory.send.bare.create()

payment_arg = algorand.create_transaction.payment(
    PaymentParams(
        sender=sender.addr,
        receiver=receiver.addr,
        amount=AlgoAmount.from_micro_algo(1),
    )
)

# Note the use of .params. here, this ensure that max_fee is still available to the composer
app_call_arg = app_client_2.params.call(
    AppClientMethodCallParams(
        method="my_other_method",
        args=[],
        max_fee=AlgoAmount.from_micro_algo(2000),
    )
)

result = (
    app_client_1.algorand
    .new_group()
    .add_app_call_method_call(
        app_client_1.params.call(
            AppClientMethodCallParams(
                method="my_method",
                args=[payment_arg, app_call_arg],
                max_fee=AlgoAmount.from_micro_algo(5000),
            )
        ),
    )
    .send(SendParams(cover_app_call_inner_transaction_fees=True))
)
```

This feature should efficiently calculate the minimum fee needed to execute an app call transaction with inners, however we always recommend testing your specific scenario behaves as expected before releasing.

#### Read-only calls

When invoking a readonly method, the transaction is simulated rather than being fully processed by the network. This allows users to call these methods without paying a fee.

Even though no actual fee is paid, the simulation still evaluates the transaction as if a fee was being paid, therefore op budget and fee coverage checks are still performed.

Because no fee is actually paid, calculating the minimum fee required to successfully execute the transaction is not required, and therefore we don't need to send an additional simulate call to calculate the minimum fee, like we do with a non readonly method call.

The behaviour of enabling `cover_app_call_inner_transaction_fees` for readonly method calls is very similar to non readonly method calls, however is subtly different as we use `max_fee` as the transaction fee when executing the readonly method call.

### Covering App Call Op Budget

The high level Algorand contract authoring languages all have support for ensuring appropriate app op budget is available via `ensure_budget` in Algorand Python, `ensureBudget` in Algorand TypeScript and `increaseOpcodeBudget` in TEALScript. This is great, as it allows contract authors to ensure appropriate budget is available by automatically sending op-up inner transactions to increase the budget available. These op-up inner transactions require the fees to be covered by an account, which is generally the responsibility of the application consumer.

Application consumers may not be immediately aware of the number of op-up inner transactions sent, so it can be difficult for them to determine the exact fees required to successfully execute an application call. Fortunately the `cover_app_call_inner_transaction_fees` setting above can be leveraged to automatically cover the fees for any op-up inner transaction that an application sends. Additionally if a contract author decides to cover the fee for an op-up inner transaction, then the application consumer will not be charged a fee for that transaction.

## Simulating a transaction

Transactions can be simulated using the simulate endpoint in algod, which enables evaluating the transaction on the network without it actually being committed to a block.
This is a powerful feature, which has a number of options which are detailed in the [simulate API docs](https://dev.algorand.co/reference/rest-apis/output/#simulatetransaction).

For example you can simulate a transaction group like below:

```python
result = (
    algorand.new_group()
    .add_payment(PaymentParams(
        sender="SENDER",
        receiver="RECEIVER",
        amount=AlgoAmount.from_micro_algo(100),
    ))
    .add_app_call_method_call(AppCallMethodCallParams(
        sender="SENDER",
        app_id=123,
        method=abi_method,
        args=[1, 2, 3],
    ))
    .simulate()
)
```

The above will execute a simulate request asserting that all transactions in the group are correctly signed.

### Simulate without signing

There are situations where you may not be able to (or want to) sign the transactions when executing simulate.
In these instances you should set `skip_signatures=True` which automatically builds empty transaction signers and sets both `fix-signers` and `allow-empty-signatures` to `True` when sending the algod API call.

For example:

```python
result = (
    algorand.new_group()
    .add_payment(PaymentParams(
        sender="SENDER",
        receiver="RECEIVER",
        amount=AlgoAmount.from_micro_algo(100),
    ))
    .add_app_call_method_call(AppCallMethodCallParams(
        sender="SENDER",
        app_id=123,
        method=abi_method,
        args=[1, 2, 3],
    ))
    .simulate(skip_signatures=True)
)
```
