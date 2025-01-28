# Algorand client

`AlgorandClient` is a client class that brokers easy access to Algorand functionality. It's the [default entrypoint](../../../README.md) into AlgoKit Utils functionality.

The main entrypoint to the bulk of the functionality in AlgoKit Utils is the `AlgorandClient` class, most of the time you can get started by typing `AlgorandClient.` and choosing one of the static initialisation methods to create an [Algorand client](todo_paste_url), e.g.:

```python
# Point to the network configured through environment variables or
#  if no environment variables it will point to the default LocalNet
#  configuration
algorand = AlgorandClient.from_environment()
# Point to default LocalNet configuration
algorand = AlgorandClient.default_local_net()
# Point to TestNet using AlgoNode free tier
algorand = AlgorandClient.testnet()
# Point to MainNet using AlgoNode free tier
algorand = AlgorandClient.mainnet()
# Point to a pre-created algod client
algorand = AlgorandClient.from_clients(algod=algod)
# Point to pre-created algod, indexer and kmd clients
algorand = AlgorandClient.from_clients(algod=algod, indexer=indexer, kmd=kmd)
# Point to custom configuration for algod
algorand = AlgorandClient.from_config(algod_config=algod_config)
# Point to custom configuration for algod, indexer and kmd
algorand = AlgorandClient.from_config(
    algod_config=algod_config,
    indexer_config=indexer_config,
    kmd_config=kmd_config,
)
```

## Accessing SDK clients

Once you have an `AlgorandClient` instance, you can access the SDK clients for the various Algorand APIs via the `algorand.client` property.

```python
algorand = AlgorandClient.default_local_net()

algod_client = algorand.client.algod
indexer_client = algorand.client.indexer
kmd_client = algorand.client.kmd
```

## Accessing manager class instances

The `AlgorandClient` has a number of manager class instances that help you quickly use intellisense to get access to advanced functionality.

- [`AccountManager`](todo_paste_url) via `algorand.account`, there are also some chainable convenience methods which wrap specific methods in `AccountManager`:
  - `algorand.set_default_signer(signer)` -
  - `algorand.set_signer_from_account(account)` -
  - `algorand.set_signer(sender, signer)`
- [`AssetManager`](todo_paste_url) via `algorand.asset`
- [`ClientManager`](todo_paste_url) via `algorand.client`

## Creating and issuing transactions

`AlgorandClient` exposes a series of methods that allow you to create, execute, and compose groups of transactions (all via the [`TransactionComposer`](todo_paste_url)).

### Creating transactions

You can compose a transaction via `algorand.create_transaction.`, which gives you an instance of the [`AlgorandClientTransactionCreator`](todo_paste_url) class. Intellisense will guide you on the different options.

The signature for the calls to send a single transaction usually look like:

```python
def method(self, *, params: ComposerTransactionTypeParams, **common_params) -> Transaction:
    """
    params: ComposerTransactionTypeParams - Transaction type specific parameters
    common_params: CommonTransactionParams - Common transaction parameters
    returns: Transaction - An unsigned algosdk.Transaction object, ready to be signed and sent
    """
```

- To get intellisense on the params, use your IDE's intellisense keyboard shortcut (e.g. ctrl+space or cmd+space).
- `ComposerTransactionTypeParams` will be the parameters that are specific to that transaction type e.g. `PaymentParams`, [see the full list](todo_paste_url)
- [`CommonTransactionParams`](todo_paste_url) are the [common transaction parameters](todo_paste_url) that can be specified for every single transaction
- `Transaction` is an unsigned `algosdk.Transaction` object, ready to be signed and sent

The return type for the ABI method call methods are slightly different:

```python
def app_call_type_method_call(self, *, params: ComposerTransactionTypeParams, **common_params) -> BuiltTransactions:
    """
    params: ComposerTransactionTypeParams - Transaction type specific parameters
    common_params: CommonTransactionParams - Common transaction parameters
    returns: BuiltTransactions - Container for transactions, method calls and signers
    """
```

Where `BuiltTransactions` looks like this:

```python
@dataclass
class BuiltTransactions:
    """Container for built transactions and associated metadata"""
    # The built transactions
    transactions: list[Transaction]
    # Any ABIMethod objects associated with any of the transactions in a dict keyed by transaction index
    method_calls: dict[int, ABIMethod]
    # Any TransactionSigner objects associated with any of the transactions in a dict keyed by transaction index
    signers: dict[int, TransactionSigner]
```

This signifies the fact that an ABI method call can actually result in multiple transactions (which in turn may have different signers), that you need ABI metadata to be able to extract the return value from the transaction result.

### Sending a single transaction

You can compose a single transaction via `algorand.send...`, which gives you an instance of the [`AlgorandClientTransactionSender`](todo_paste_url) class. Intellisense will guide you on the different options.

Further documentation is present in the related capabilities:

- [App management](todo_paste_url)
- [Asset management](todo_paste_url)
- [Algo transfers](todo_paste_url)

The signature for the calls to send a single transaction usually look like:

```python
def method(self, *, params: ComposerTransactionTypeParams, **common_params) -> SingleSendTransactionResult:
    """
    params: ComposerTransactionTypeParams - Transaction type specific parameters
    common_params: CommonAppCallParams & SendParams - Common parameters for app calls and transaction sending
    returns: SingleSendTransactionResult - Result of sending a single transaction
    """
```

- To get intellisense on the params, use your IDE's intellisense keyboard shortcut (e.g. ctrl+space).
- `ComposerTransactionTypeParams` will be the parameters that are specific to that transaction type e.g. `PaymentParams`, [see the full list](todo_paste_url)
- [`CommonAppCallParams`](todo_paste_url) are the [common app call transaction parameters](todo_paste_url) that can be specified for every single app transaction
- [`SendParams`](todo_paste_url) are the [parameters](todo_paste_url) that control execution semantics when sending transactions to the network
- [`SendSingleTransactionResult`](todo_paste_url) is all of the information that is relevant when [sending a single transaction to the network](todo_paste_url)

Generally, the functions to immediately send a single transaction will emit log messages before and/or after sending the transaction. You can opt-out of this by sending `suppress_log=True`.

### Composing a group of transactions

You can compose a group of transactions for execution by using the `new_group()` method on `AlgorandClient` and then use the various `.add_{type}()` methods on [`TransactionComposer`](todo_paste_url) to add a series of transactions.

```python
result = (
    algorand
    .new_group()
    .add_payment(
        sender="SENDERADDRESS",
        receiver="RECEIVERADDRESS",
        amount=microalgos(1)
    )
    .add_asset_opt_in(sender="SENDERADDRESS", asset_id=12345)
    .send()
)
```

`new_group()` returns a new [`TransactionComposer`](todo_paste_url) instance, which can also return the group of transactions, simulate them and other things.

### Transaction parameters

To create a transaction you define a set of parameters as a Python params dataclass instance.

The type [`TxnParams`](todo_paste_url) is a union type representing all of the transaction parameters that can be specified for constructing any Algorand transaction type.

- `sender: str` - The address of the account sending the transaction
- `signer: TransactionSigner | TransactionSignerAccountProtocol | None` - The function used to sign transaction(s); if not specified then an attempt will be made to find a registered signer for the given `sender` or use a default signer (if configured)
- `rekey_to: Optional[str]` - Change the signing key of the sender to the given address. **Warning:** Please be careful and read the [official rekey guidance](https://developer.algorand.org/docs/get-details/accounts/rekey/)
- `note: Optional[bytes | str]` - Note to attach to transaction (UTF-8 encoded if string). Max 1000 bytes
- `lease: Optional[bytes | str]` - Prevent duplicate transactions with same lease (max 32 bytes). [Lease documentation](https://developer.algorand.org/articles/leased-transactions-securing-advanced-smart-contract-design/)
- Fee management:
  - `static_fee: Optional[AlgoAmount]` - Fixed transaction fee (use `extra_fee` instead unless setting to 0)
  - `extra_fee: Optional[AlgoAmount]` - Additional fee to cover inner transactions
  - `max_fee: Optional[AlgoAmount]` - Maximum allowed fee (prevents overspending during congestion)
- Validity management:

  - `validity_window: Optional[int]` - Number of rounds transaction is valid (default: 10)
  - `first_valid_round: Optional[int]` - Explicit first valid round (use with caution)
  - `last_valid_round: Optional[int]` - Explicit last valid round (prefer `validity_window`)

- [`SendParams`](todo_paste_url)
  - `max_rounds_to_wait_for_confirmation: Optional[int]` - Maximum rounds to wait for confirmation
  - `suppress_log: bool` - Suppress log messages (default: False)
  - `populate_app_call_resources: bool` - Auto-populate app call resources using simulation (default: from config)
  - `cover_app_call_inner_transaction_fees: bool` - Automatically cover inner transaction fees via simulation

Some more transaction-specific parameters extend these base types:

#### Payment Transactions (`PaymentParams`)

- `receiver: str` - Recipient address
- `amount: AlgoAmount` - Amount to send
- `close_remainder_to: Optional[str]` - Address to send remaining funds to (for account closure)

#### Asset Transactions

- `AssetTransferParams`: Asset transfers including opt-in
- `AssetCreateParams`: Asset creation
- `AssetConfigParams`: Asset configuration
- `AssetFreezeParams`: Asset freezing
- `AssetDestroyParams`: Asset destruction

#### Application Transactions

- `AppCallParams`: Generic application calls
- `AppCreateParams`: Application creation
- `AppUpdateParams`: Application update
- `AppDeleteParams`: Application deletion

#### Key Registration

- `OnlineKeyRegistrationParams`: Register online participation keys
- `OfflineKeyRegistrationParams`: Take account offline

Usage example with `AlgorandClient`:

```python
# Create transaction
payment = client.create_transaction.payment(
    PaymentParams(sender=account.address, receiver=receiver, amount=AlgoAmount(1))
)

# Send transaction
result = client.send.send_transaction(payment, SendParams())
```

These parameters are used with the [`TransactionComposer`](todo_paste_url) class which handles:

- Automatic fee calculation
- Validity window management
- Transaction grouping
- ABI method handling
- Simulation-based resource population

### Transaction configuration

AlgorandClient caches network provided transaction values for you automatically to reduce network traffic. It has a set of default configurations that control this behaviour, but you have the ability to override and change the configuration of this behaviour:

- `algorand.set_default_validity_window(validity_window)` - Set the default validity window (number of rounds from the current known round that the transaction will be valid to be accepted for), having a smallish value for this is usually ideal to avoid transactions that are valid for a long future period and may be submitted even after you think it failed to submit if waiting for a particular number of rounds for the transaction to be successfully submitted. The validity window defaults to `10`, except localnet environments where it's set to `1000`.
- `algorand.set_suggested_params(suggested_params, until=None)` - Set the suggested network parameters to use (optionally until the given time)
- `algorand.set_suggested_params_timeout(timeout)` - Set the timeout that is used to cache the suggested network parameters (by default 3 seconds)
- `algorand.get_suggested_params()` - Get the current suggested network parameters object, either the cached value, or if the cache has expired a fresh value
