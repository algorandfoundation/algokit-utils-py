# Algorand client

`AlgorandClient` is a client class that brokers easy access to Algorand functionality. It's the default entrypoint into AlgoKit Utils functionality.

The main entrypoint to the bulk of the functionality in AlgoKit Utils is the `AlgorandClient` class. You can get started by using one of the static initialization methods to create an Algorand client:

```python
# Point to the network configured through environment variables or
# if no environment variables it will point to the default LocalNet configuration
algorand = AlgorandClient.from_environment()
# Point to default LocalNet configuration
algorand = AlgorandClient.default_local_net()
# Point to TestNet using AlgoNode free tier
algorand = AlgorandClient.test_net()
# Point to MainNet using AlgoNode free tier
algorand = AlgorandClient.main_net()
# Point to a pre-created algod client(s)
algorand = AlgorandClient.from_clients(
    AlgoSdkClients(
        algod=...,
        indexer=...,
        kmd=...,
    )
)
# Point to custom configuration
algorand = AlgorandClient.from_config(
    AlgoClientConfigs(
        algod_config=AlgoClientConfig(
            server="http://localhost:4001", token="my-token", port=4001
        ),
        indexer_config=None,
        kmd_config=None,
    )
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

The `AlgorandClient` has several manager class instances that help you quickly access advanced functionality:

- `AccountManager` via `algorand.account`, with chainable convenience methods:
  - `algorand.set_default_signer(signer)`
  - `algorand.set_signer(sender, signer)`
- `AssetManager` via `algorand.asset`
- `ClientManager` via `algorand.client`
- `AppManager` via `algorand.app`
- `AppDeployer` via `algorand.app_deployer`

## Creating and issuing transactions

`AlgorandClient` exposes methods to create, execute, and compose groups of transactions via the `TransactionComposer`.

### Transaction configuration

AlgorandClient caches network provided transaction values automatically to reduce network traffic. You can configure this behavior:

- `algorand.set_default_validity_window(validity_window)` - Set the default validity window (number of rounds the transaction will be valid). Defaults to 10.
- `algorand.set_suggested_params(suggested_params, until?)` - Set the suggested network parameters to use (optionally until the given time)
- `algorand.set_suggested_params_timeout(timeout)` - Set the timeout for caching suggested network parameters (default 3 seconds)
- `algorand.get_suggested_params()` - Get current suggested network parameters

### Creating transaction groups

You can compose a group of transactions using the `new_group()` method which returns a `TransactionComposer` instance:

```python
result = (
    algorand.new_group()
    .add_payment(sender="SENDERADDRESS", receiver="RECEIVERADDRESS", amount=1_000)
    .add_asset_opt_in(sender="SENDERADDRESS", asset_id=12345)
    .send()
)
```

### Transaction Parameters

Common transaction parameters in Python follow similar patterns to TypeScript but use Python idioms:

- Sender addresses are passed as strings
- Amounts are typically passed as integers (microAlgos)
- Signers can be `algosdk.TransactionSigner` instances
- Notes and leases can be `bytes` or `str`
- Fee management uses integers for microAlgos
- Round validity uses integers for round numbers
