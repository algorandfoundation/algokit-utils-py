# AlgoKit Utils Python: v5 Migration Guide

## Overview

Version 5 represents a **major architectural overhaul** of AlgoKit Utils for Python. The library has been decoupled from `py-algorand-sdk` (`algosdk`) and restructured into a multi-module package with custom-generated API clients. This enables:

- **No algosdk dependency** — The library now uses generated clients and first-party transaction primitives instead of `algosdk`
- **Unified AlgorandClient** — Still the single entry point for all Algorand interactions
- **Type-safe generated clients** — Algod, Indexer, and KMD clients are generated from OpenAPI specs with full typing
- **Cross-SDK alignment** — Naming conventions aligned with `algokit-utils-ts` for consistency across the Algorand SDK ecosystem

This guide covers both developers migrating their applications and the specific changes needed at each layer of the API.

> **Who is this for?** If you are using `algokit-utils` v4 (including any legacy v2 APIs still available in v4), this guide will walk you through every breaking change.

---

## Quick Reference Tables

### Entry Points

| v4                                  | v5                                   | Notes                   |
| :---------------------------------- | :----------------------------------- | :---------------------- |
| `AlgorandClient.default_localnet()` | `AlgorandClient.default_localnet()`  | Unchanged               |
| `AlgorandClient.testnet()`          | `AlgorandClient.testnet()`           | Unchanged               |
| `AlgorandClient.mainnet()`          | `AlgorandClient.mainnet()`           | Unchanged               |
| `AlgorandClient.from_environment()` | `AlgorandClient.from_environment()`  | Unchanged               |
| `get_algod_client()`                | **Removed** — use `AlgorandClient.*` | Legacy function deleted |
| `get_indexer_client()`              | **Removed** — use `AlgorandClient.*` | Legacy function deleted |

### Common Operations

| Operation      | v4 (legacy)                                    | v4 (modern) / v5                                          |
| :------------- | :--------------------------------------------- | :-------------------------------------------------------- |
| Payment        | `transfer(TransferParameters(...))`            | `algorand.send.payment(PaymentParams(...))`               |
| Asset transfer | `transfer_asset(TransferAssetParameters(...))` | `algorand.send.asset_transfer(AssetTransferParams(...))`  |
| Asset opt-in   | `opt_in(algod, account, asset_id)`             | `algorand.send.asset_opt_in(AssetOptInParams(...))`       |
| Ensure funded  | `ensure_funded(EnsureBalanceParameters(...))`  | `algorand.account.ensure_funded(addr, dispenser, amount)` |
| App deploy     | `app_client.deploy(...)`                       | `app_factory.deploy(...)`                                 |
| App call       | `ApplicationClient.call(...)`                  | `app_client.send.call(...)`                               |

### Naming Standardizations

| v4                                     | v5                               | Notes                |
| :------------------------------------- | :------------------------------- | :------------------- |
| `SigningAccount`                       | `AddressWithSigners`             | `.address` → `.addr` |
| `TransactionSignerAccountProtocol`     | `AddressWithTransactionSigner`   | `.address` → `.addr` |
| `MultisigMetadata.addresses`           | `MultisigMetadata.addrs`         | Field renamed        |
| `MultiSigAccount`                      | `MultisigAccount`                | Class renamed        |
| `SendAtomicTransactionComposerResults` | `SendTransactionComposerResults` | Class renamed        |
| `SourceMap`                            | `ProgramSourceMap`               | Class renamed        |
| `OnComplete.NoOpOC`                    | `OnApplicationComplete.NoOp`     | Enum renamed         |
| `populate_app_call_resources`          | `populate_group_resources`       | Function renamed     |

---

## Part 1: Architecture Changes

### 1.1 New Package Structure

v4 was a single `algokit_utils` package that depended on `py-algorand-sdk`. v5 bundles 8 top-level Python modules into a single `algokit-utils` distribution:

| Module                   | Purpose                                                    | Replaces                                                     |
| :----------------------- | :--------------------------------------------------------- | :----------------------------------------------------------- |
| `algokit_utils`          | High-level orchestration (AlgorandClient, AppClient, etc.) | Slimmed down from v4                                         |
| `algokit_transact`       | Transaction building, signing, encoding                    | `algosdk.transaction`, `algosdk.atomic_transaction_composer` |
| `algokit_algod_client`   | Typed Algod REST client (OAS-generated)                    | `algosdk.v2client.algod.AlgodClient`                         |
| `algokit_indexer_client` | Typed Indexer REST client (OAS-generated)                  | `algosdk.v2client.indexer.IndexerClient`                     |
| `algokit_kmd_client`     | Typed KMD REST client (OAS-generated)                      | `algosdk.kmd.KMDClient`                                      |
| `algokit_abi`            | ABI encoding/decoding, ARC-32/ARC-56 app specs             | `algosdk.abi` + custom ARC code                              |
| `algokit_algo25`         | Mnemonic/key generation (25-word scheme)                   | `algosdk.mnemonic`                                           |
| `algokit_common`         | Shared primitives (address, hashing, constants)            | Various `algosdk` internals                                  |

All 8 modules install together via `pip install algokit-utils`. You can import directly from any module:

```python
# High-level (most common)
from algokit_utils import AlgorandClient, AppClient, PaymentParams

# Or import from specific modules
from algokit_transact import Transaction, TransactionType, OnApplicationComplete
from algokit_algod_client import AlgodClient
from algokit_abi.arc56 import Arc56Contract
from algokit_algo25 import mnemonic_from_seed
```

### 1.2 Build System Change

The project build system has changed from **Poetry** to **uv**:

- `poetry.lock` → `uv.lock`
- Build backend: `poetry-core` → `uv_build`

If you are contributing to algokit-utils-py, you'll need to install [uv](https://docs.astral.sh/uv/) instead of Poetry.

### 1.3 Dependency Changes

**Removed:**

- `py-algorand-sdk` (`algosdk`) — completely removed

**Added:**

- `httpx` — HTTP client for generated API clients
- `msgpack` / `msgpack-types` — MessagePack encoding (previously via algosdk)
- `pynacl` — Ed25519 signing (previously via algosdk)
- `pycryptodomex` — Cryptographic operations (previously via algosdk)

If your code imports from `algosdk` directly, you will need to replace all those imports with the equivalent `algokit_*` module.

### 1.4 Import Path Migration

| What you need      | v4 import                                                             | v5 import                                                                     |
| :----------------- | :-------------------------------------------------------------------- | :---------------------------------------------------------------------------- |
| Algod client       | `from algosdk.v2client.algod import AlgodClient`                      | `from algokit_algod_client import AlgodClient`                                |
| Indexer client     | `from algosdk.v2client.indexer import IndexerClient`                  | `from algokit_indexer_client import IndexerClient`                            |
| KMD client         | `from algosdk.kmd import KMDClient`                                   | `from algokit_kmd_client import KmdClient`                                    |
| Transaction types  | `from algosdk.transaction import PaymentTxn`                          | `from algokit_transact import Transaction, PaymentTransactionFields`          |
| Transaction signer | `from algosdk.atomic_transaction_composer import TransactionSigner`   | `from algokit_transact import TransactionSigner`                              |
| OnComplete         | `from algosdk.transaction import OnComplete`                          | `from algokit_transact import OnApplicationComplete`                          |
| Mnemonics          | `from algosdk import mnemonic`                                        | `from algokit_algo25 import mnemonic_from_seed, seed_from_mnemonic`           |
| ABI types          | `from algosdk.abi import ABIType`                                     | `from algokit_abi.abi import ...`                                             |
| ARC-56 spec        | `from algokit_utils.applications.app_spec.arc56 import Arc56Contract` | `from algokit_abi.arc56 import Arc56Contract`                                 |
| ARC-32 spec        | `from algokit_utils.applications.app_spec.arc32 import Arc32Contract` | `from algokit_abi.arc32 import Arc32Contract`                                 |
| Address utilities  | `from algosdk import encoding`                                        | `from algokit_common import address_from_public_key, public_key_from_address` |
| Constants          | `from algosdk import constants`                                       | `from algokit_common import MIN_TXN_FEE, ZERO_ADDRESS`                        |
| Source map         | `from algosdk.source_map import SourceMap`                            | `from algokit_common import ProgramSourceMap`                                 |

You can also access most transaction types via the `algokit_utils.transact` facade:

```python
# These are equivalent:
from algokit_transact import Transaction, OnApplicationComplete
from algokit_utils.transact import Transaction, OnApplicationComplete
```

---

## Part 2: Client Changes

### 2.1 AlgorandClient

`AlgorandClient` remains the primary entry point. Its public API is largely unchanged:

```python
from algokit_utils import AlgorandClient

# These all work the same as v4
algorand = AlgorandClient.default_localnet()
algorand = AlgorandClient.testnet()
algorand = AlgorandClient.mainnet()
algorand = AlgorandClient.from_environment()
```

The internal client types have changed (see below), but if you only interact through `AlgorandClient`, most of your code should continue to work.

### 2.2 Algod/Indexer/KMD Client Types

The underlying client types are now generated from OpenAPI specs instead of coming from `algosdk`:

```python
# v4
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from algosdk.kmd import KMDClient

# v5
from algokit_algod_client import AlgodClient
from algokit_indexer_client import IndexerClient
from algokit_kmd_client import KmdClient  # Note: lowercase 'md'
```

If you access raw clients via `algorand.client.algod`, the returned type is now `algokit_algod_client.AlgodClient` instead of `algosdk.v2client.algod.AlgodClient`. Update any type annotations accordingly.

### 2.3 Client Configuration

Client configuration types are now per-package:

```python
# v4
from algokit_utils.models.network import AlgoClientNetworkConfig

# v5 — AlgoClientNetworkConfig still works, but underlying clients use:
from algokit_algod_client import ClientConfig as AlgodClientConfig
from algokit_indexer_client import ClientConfig as IndexerClientConfig
from algokit_kmd_client import ClientConfig as KmdClientConfig
```

### 2.4 SuggestedParams Changes

The `SuggestedParams` type now comes from the generated Algod client with different field names:

```python
# v4 (algosdk)
params.gen   # genesis ID
params.gh    # genesis hash

# v5 (algokit_algod_client)
params.genesis_id    # genesis ID
params.genesis_hash  # genesis hash
```

### 2.5 ClientManager.close()

v5 adds a `close()` method to `ClientManager` for properly closing HTTP connections (the generated clients use `httpx`):

```python
algorand = AlgorandClient.default_localnet()
# ... use the client ...
algorand.client.close()  # Clean up HTTP connections
```

---

## Part 3: Account and Signer Changes

### 3.1 SigningAccount → AddressWithSigners

The primary account type has been renamed for cross-SDK alignment:

```python
# v4
from algokit_utils import SigningAccount

account = SigningAccount(private_key=key)
print(account.address)  # string address

# v5
from algokit_transact import AddressWithSigners

# Or generate via AlgorandClient (recommended)
account = algorand.account.random()
print(account.addr)  # .address → .addr
```

### 3.2 TransactionSignerAccountProtocol → AddressWithTransactionSigner

```python
# v4
from algokit_utils import TransactionSignerAccountProtocol

def my_function(account: TransactionSignerAccountProtocol):
    print(account.address)

# v5
from algokit_transact import AddressWithTransactionSigner

def my_function(account: AddressWithTransactionSigner):
    print(account.addr)  # .address → .addr
```

### 3.3 MultisigAccount/MultisigMetadata Relocation and Renames

These types have moved to `algokit_transact` with naming changes:

```python
# v4
from algokit_utils.models.account import MultiSigAccount, MultisigMetadata

metadata = MultisigMetadata(version=1, threshold=2, addresses=["addr1", "addr2"])
msig = MultiSigAccount(metadata, [signer1, signer2])

# v5
from algokit_transact import MultisigAccount, MultisigMetadata

metadata = MultisigMetadata(version=1, threshold=2, addrs=["addr1", "addr2"])  # .addresses → .addrs
msig = MultisigAccount(metadata, [signer1, signer2])  # MultiSigAccount → MultisigAccount
```

Backward-compatible re-exports exist via `algokit_utils.transact` and `algokit_utils.models.account`.

### 3.4 LogicSigAccount Relocation

```python
# v4
from algokit_utils.models.account import LogicSigAccount

# v5
from algokit_transact import LogicSigAccount

# Or via AlgorandClient
lsig_account = algorand.account.logicsig(program)
```

### 3.5 New Signer Types

v5 introduces a richer signer hierarchy from `algokit_transact`:

| Type                  | Purpose                                               |
| :-------------------- | :---------------------------------------------------- |
| `TransactionSigner`   | Signs transactions (callable protocol, no longer ABC) |
| `BytesSigner`         | Signs raw bytes                                       |
| `ProgramDataSigner`   | Signs program data                                    |
| `MxBytesSigner`       | Signs MX-prefixed bytes                               |
| `DelegatedLsigSigner` | Creates delegated logic signatures                    |
| `AddressWithSigners`  | Address + all signer types bundled together           |

---

## Part 4: Transaction Changes

### 4.1 OnApplicationComplete Enum

The `OnComplete` enum from `algosdk` is replaced by `OnApplicationComplete` from `algokit_transact`:

```python
# v4
from algosdk.transaction import OnComplete

on_complete = OnComplete.NoOpOC
on_complete = OnComplete.OptInOC
on_complete = OnComplete.CloseOutOC
on_complete = OnComplete.ClearStateOC
on_complete = OnComplete.UpdateApplicationOC
on_complete = OnComplete.DeleteApplicationOC

# v5
from algokit_transact import OnApplicationComplete

on_complete = OnApplicationComplete.NoOp
on_complete = OnApplicationComplete.OptIn
on_complete = OnApplicationComplete.CloseOut
on_complete = OnApplicationComplete.ClearState
on_complete = OnApplicationComplete.UpdateApplication
on_complete = OnApplicationComplete.DeleteApplication
```

### 4.2 TransactionSigner

The `TransactionSigner` is now a callable protocol instead of an abstract base class:

```python
# v4
from algosdk.atomic_transaction_composer import TransactionSigner  # ABC with .sign_transactions()

# v5
from algokit_transact import TransactionSigner  # Callable protocol
```

### 4.3 TransactionComposer Changes

The `TransactionComposer` constructor now takes a `TransactionComposerParams` dataclass:

```python
# v4
composer = TransactionComposer(
    algod=algod_client,
    get_signer=get_signer_fn,
    get_suggested_params=get_params_fn,
)

# v5
from algokit_utils.transactions import TransactionComposer, TransactionComposerParams

composer = TransactionComposer(
    params=TransactionComposerParams(
        algod=algod_client,
        get_signer=get_signer_fn,
        get_suggested_params=get_params_fn,
    )
)
```

Result types have been renamed:

```python
# v4
from algokit_utils import SendAtomicTransactionComposerResults

# v5
from algokit_utils import SendTransactionComposerResults
```

### 4.4 Transaction Parameter Types

Transaction parameter dataclasses have moved to `algokit_utils.transactions.types`:

```python
from algokit_utils import (
    PaymentParams,
    AssetCreateParams,
    AssetTransferParams,
    AssetOptInParams,
    AssetOptOutParams,
    AppCallParams,
    AppCreateParams,
    AppUpdateParams,
    AppDeleteParams,
    OnlineKeyRegistrationParams,
    OfflineKeyRegistrationParams,
)
```

The types themselves (`PaymentParams`, `AppCallParams`, etc.) keep the same names and fields.

### 4.5 New Transaction Builders

v5 adds a `transactions/builders/` package with functions for constructing low-level `algokit_transact.Transaction` objects:

```python
from algokit_utils.transactions.builders import (
    build_payment_transaction,
    build_app_call_transaction,
    build_app_create_transaction,
    build_asset_create_transaction,
    build_asset_transfer_transaction,
    build_asset_opt_in_transaction,
    # ... etc.
)
```

These are useful when you need fine-grained control over transaction construction at the `algokit_transact` level.

### 4.6 Resource Population

```python
# v4
from algokit_utils import populate_app_call_resources

# v5
from algokit_utils.transactions.composer_resources import (
    populate_group_resources,
    populate_transaction_resources,
)
```

The helper functions `prepare_group_for_sending` and `send_atomic_transaction_composer` have been removed from the public API.

### 4.7 Fee Types

New types for fee management:

```python
from algokit_utils.transactions.fee_coverage import FeeDelta, FeePriority
```

---

## Part 5: App Client and Smart Contract Changes

### 5.1 Legacy ApplicationClient Removed

The old `ApplicationClient` class from `_legacy_v2` has been completely removed:

```python
# v4 (legacy)
from algokit_utils import ApplicationClient

app_client = ApplicationClient(algod_client, app_spec, sender=account)
result = app_client.call("hello", name="world")

# v5 — use AppClient and AppFactory instead
from algokit_utils import AlgorandClient

algorand = AlgorandClient.default_localnet()

# For deploying new apps, use AppFactory
factory = algorand.client.get_app_factory(app_spec=arc56_spec, default_sender=sender)
app_client, result = factory.deploy(...)

# For interacting with existing apps, use AppClient
app_client = algorand.client.get_app_client_by_id(app_spec=arc56_spec, app_id=app_id, default_sender=sender)
result = app_client.send.call(method="hello", args=["world"])
```

### 5.2 ApplicationSpecification Removed

The old `ApplicationSpecification` class is no longer accepted:

```python
# v4
from algokit_utils import ApplicationSpecification

spec = ApplicationSpecification(...)

# v5 — use Arc56Contract (ARC-32 specs are auto-converted)
from algokit_abi.arc56 import Arc56Contract
from algokit_abi.arc32 import Arc32Contract
```

`get_app_factory()` and `get_app_client_by_id()` now only accept `Arc56Contract | str`, not `ApplicationSpecification`.

### 5.3 App Spec Location

ARC-32 and ARC-56 contract specifications have moved to the `algokit_abi` package:

```python
# v4
from algokit_utils.applications.app_spec.arc56 import Arc56Contract
from algokit_utils.applications.app_spec.arc32 import Arc32Contract

# v5
from algokit_abi.arc56 import Arc56Contract
from algokit_abi.arc32 import Arc32Contract

# Still re-exported for convenience:
from algokit_utils.applications.app_spec import Arc56Contract, Arc32Contract
```

### 5.4 Confirmation Results

Transaction confirmation results are now typed objects instead of dictionaries:

```python
# v4 — dict-style access
result = algorand.send.payment(PaymentParams(...))
app_id = result.confirmation["application-index"]
asset_id = result.confirmation["asset-index"]

# v5 — typed attribute access
result = algorand.send.payment(PaymentParams(...))
app_id = result.confirmation.app_id
asset_id = result.confirmation.asset_id
```

The `confirmation` field is now `algod_models.PendingTransactionResponse` (a typed dataclass) instead of `AlgodResponseType` (a dict-like object).

---

## Part 6: ABI Changes

### 6.1 Return Type Changes

ABI decoding now returns more Pythonic types:

| ABI Type                               | v4 returns  | v5 returns        |
| :------------------------------------- | :---------- | :---------------- |
| `byte`, `byte[]`, `byte[n]`            | `list[int]` | `bytes`           |
| `ufixed<N>x<M>`                        | `int`       | `decimal.Decimal` |
| Tuple types (e.g., `(uint64,address)`) | `list`      | `tuple`           |

If your code processes ABI return values, update type expectations:

```python
# v4
result = app_client.call("get_bytes")
byte_list: list[int] = result.return_value  # [72, 101, 108, 108, 111]

# v5
result = app_client.send.call(method="get_bytes")
byte_data: bytes = result.abi_return.return_value  # b"Hello"
```

### 6.2 Encoding Changes

| ABI Type        | v4 accepts | v5 accepts                 |
| :-------------- | :--------- | :------------------------- |
| `byte`          | `int`      | `bytes` or `int`           |
| `ufixed<N>x<M>` | `int`      | `decimal.Decimal` or `int` |

---

## Part 7: Generated Client Model Changes

### 7.1 Block Model Restructuring

Block models from the generated Algod client have been reorganized:

```python
# v4
from algokit_algod_client.models import GetBlock

response: GetBlock = algod_client.get_block(...)
fee_sink = response.block.header.fee_sink
protocol = response.block.header.current_protocol
proposal = response.block.header.upgrade_propose
tx_root = response.block.header.transactions_root

# v5
from algokit_algod_client.models import BlockResponse

response: BlockResponse = algod_client.get_block(...)
fee_sink = response.block.header.reward_state.fee_sink
protocol = response.block.header.upgrade_state.current_protocol
proposal = response.block.header.upgrade_vote.upgrade_propose
tx_root = response.block.header.txn_commitments.transactions_root
```

Header fields have been reorganized into nested types:

- Reward fields → `header.reward_state.*`
- Protocol fields → `header.upgrade_state.*`
- Upgrade vote fields → `header.upgrade_vote.*`
- Transaction root fields → `header.txn_commitments.*`

Other changes:

- `BlockEvalDelta.bytes` → `BlockEvalDelta.bytes_value` (avoids Python keyword conflict)
- `previous_block_hash` and `genesis_hash` are now non-optional with `bytes(32)` defaults

### 7.2 Fixed-Length Byte Validation

v5 enforces runtime validation for fixed-length byte fields (32 and 64 bytes). Fields that previously accepted any length now raise `ValueError`:

```python
# v4 — silently accepted wrong lengths
txn.group = bytes(10)  # No error

# v5 — raises ValueError
txn.group = bytes(10)  # ValueError: Expected 32 bytes, got 10
txn.group = bytes(32)  # OK
```

Affected fields: `group`, `lease`, transaction hashes, block hashes, keys (32 bytes), signatures, SHA-512 hashes (64 bytes).

### 7.3 Confirmation/Response Type Changes

Response types from the generated Algod client are now proper typed dataclasses. If you were accessing responses as dictionaries (e.g., `response["key"]`), switch to attribute access (e.g., `response.key`).

---

## Part 8: Utility Changes

### 8.1 Common Utilities

The `algokit_common` module provides constants and functions that were previously scattered across `algosdk`:

```python
from algokit_common import (
    # Constants
    ADDRESS_LENGTH,
    CHECKSUM_BYTE_LENGTH,
    HASH_BYTES_LENGTH,
    MAX_TRANSACTION_GROUP_SIZE,
    MICROALGOS_TO_ALGOS_RATIO,
    MIN_TXN_FEE,
    PUBLIC_KEY_BYTE_LENGTH,
    SIGNATURE_BYTE_LENGTH,
    TRANSACTION_ID_LENGTH,
    ZERO_ADDRESS,

    # Functions
    address_from_public_key,
    get_application_address,
    public_key_from_address,
    sha512_256,

    # Source map
    ProgramSourceMap,
)
```

These are also accessible via `algokit_utils.common`.

### 8.2 SourceMap → ProgramSourceMap

```python
# v4
from algosdk.source_map import SourceMap

# v5
from algokit_common import ProgramSourceMap
```

### 8.3 AlgoAmount Enhancements

`AlgoAmount` now supports full comparison operations and accepts `int` in arithmetic:

```python
from algokit_utils import AlgoAmount

a = AlgoAmount.from_algo(5)
b = AlgoAmount.from_algo(3)

# New in v5: full comparison support
assert a > b
assert a >= b
assert b < a

# New in v5: arithmetic with int (treated as micro-algos)
result = a + 1_000_000  # adds 1 Algo worth of micro-algos
result = a - 500_000
```

### 8.4 Mnemonic Utilities

Mnemonic operations are now in the `algokit_algo25` package:

```python
# v4
from algosdk import mnemonic

words = mnemonic.from_private_key(private_key)
key = mnemonic.to_private_key(words)

# v5
from algokit_algo25 import (
    mnemonic_from_seed,
    seed_from_mnemonic,
    secret_key_to_mnemonic,
    master_derivation_key_to_mnemonic,
    mnemonic_to_master_derivation_key,
)

words = secret_key_to_mnemonic(secret_key)
seed = seed_from_mnemonic(words)
```

Also accessible via `algokit_utils.algo25`.

---

## Part 9: Removed/Deprecated APIs

### 9.1 Removed Legacy v2 Functions

| Removed Function                     | v5 Replacement                                                    |
| :----------------------------------- | :---------------------------------------------------------------- |
| `get_algod_client()`                 | `AlgorandClient.default_localnet()` / `.testnet()` / `.mainnet()` |
| `get_indexer_client()`               | Access via `algorand.client.indexer`                              |
| `get_kmd_client_from_algod_client()` | Access via `algorand.client.kmd`                                  |
| `get_account()`                      | `algorand.account.from_environment(name)`                         |
| `get_account_from_mnemonic()`        | `algorand.account.from_mnemonic(mnemonic)`                        |
| `get_localnet_default_account()`     | `algorand.account.localnet_dispenser()`                           |
| `get_dispenser_account()`            | `algorand.account.dispenser_from_environment()`                   |
| `create_kmd_wallet_account()`        | `algorand.account.from_kmd(...)`                                  |
| `get_or_create_kmd_wallet_account()` | `algorand.account.from_kmd(...)`                                  |
| `get_kmd_wallet_account()`           | `algorand.account.from_kmd(...)`                                  |
| `ensure_funded()`                    | `algorand.account.ensure_funded(addr, dispenser, amount)`         |
| `transfer()`                         | `algorand.send.payment(PaymentParams(...))`                       |
| `transfer_asset()`                   | `algorand.send.asset_transfer(AssetTransferParams(...))`          |
| `opt_in()`                           | `algorand.send.asset_opt_in(AssetOptInParams(...))`               |
| `opt_out()`                          | `algorand.send.asset_opt_out(AssetOptOutParams(...))`             |
| `is_localnet()`                      | `algorand.client.network` returns `NetworkDetail`                 |
| `is_mainnet()`                       | `algorand.client.network.is_mainnet`                              |
| `is_testnet()`                       | `algorand.client.network.is_testnet`                              |
| `execute_atc_with_logic_error()`     | Use `TransactionComposer` directly                                |
| `get_next_version()`                 | Internal to deploy logic                                          |
| `get_sender_from_signer()`           | No longer needed                                                  |
| `num_extra_program_pages()`          | `calculate_extra_program_pages()` in `transactions/helpers.py`    |
| `replace_template_variables()`       | Internal to deploy logic                                          |
| `get_app_id_from_tx_id()`            | Access `result.app_id` from send result                           |
| `get_creator_apps()`                 | Use `AppDeployer` directly                                        |

### 9.2 Removed Legacy v2 Classes

| Removed Class                                                      | v5 Replacement                                                                                |
| :----------------------------------------------------------------- | :-------------------------------------------------------------------------------------------- |
| `ApplicationClient`                                                | `AppClient` / `AppFactory` via `algorand.client.get_app_client_by_id()` / `get_app_factory()` |
| `ApplicationSpecification`                                         | `Arc56Contract` from `algokit_abi`                                                            |
| `Account` (NamedTuple)                                             | `AddressWithSigners` from `algokit_transact`                                                  |
| `Program`                                                          | Compile via `AppClient` or `AppManager`                                                       |
| `AlgoClientConfig`                                                 | `AlgoClientNetworkConfig`                                                                     |
| `ABITransactionResponse`                                           | Typed result objects from `.send.*()` calls                                                   |
| `CommonCallParameters` / `CommonCallParametersDict`                | `CommonTxnParams`                                                                             |
| `CreateCallParameters` / `CreateCallParametersDict`                | `AppCreateParams`                                                                             |
| `TransactionParameters` / `TransactionParametersDict`              | Specific param types (`PaymentParams`, etc.)                                                  |
| `OnCompleteCallParameters`                                         | `AppCallParams` with `on_complete` field                                                      |
| `EnsureBalanceParameters`                                          | `algorand.account.ensure_funded()` params                                                     |
| `EnsureFundedResponse`                                             | Typed result from `ensure_funded()`                                                           |
| `TransferParameters`                                               | `PaymentParams`                                                                               |
| `TransferAssetParameters`                                          | `AssetTransferParams`                                                                         |
| `AppDeployMetaData` / `AppMetaData` / `AppLookup` / `AppReference` | Internal to `AppDeployer`                                                                     |
| `DeployResponse` / `DeploymentFailedError`                         | Result types from `AppFactory.deploy()`                                                       |
| `ABICallArgs` / `DeployCallArgs` / `DeployCreateCallArgs`          | Method call params in `AppFactory`                                                            |
| `MethodHints` / `MethodConfigDict` / `CallConfig`                  | ARC-56 natively handles these                                                                 |
| `TemplateValueDict` / `TemplateValueMapping`                       | `deploy_time_params` in `AppFactory`                                                          |

### 9.3 Removed Beta Shims

The `algokit_utils.beta` package (which contained deprecation-warning shims for `account_manager`, `algorand_client`, `client_manager`, `composer`) is removed. Import directly from `algokit_utils` instead:

```python
# v4 (beta imports — deprecated)
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AccountManager
from algokit_utils.beta.composer import TransactionComposer

# v5 (direct imports)
from algokit_utils import AlgorandClient
from algokit_utils.accounts import AccountManager
from algokit_utils.transactions import TransactionComposer
```

### 9.4 Removed Top-Level Shim Modules

These files that re-exported legacy v2 code with deprecation warnings are deleted:

- `algokit_utils.account`
- `algokit_utils.application_client`
- `algokit_utils.application_specification`
- `algokit_utils.asset`
- `algokit_utils.deploy`
- `algokit_utils.dispenser_api`
- `algokit_utils.logic_error`
- `algokit_utils.network_clients`

---

## Migration Checklist

### Step 1: Update Dependencies

```bash
# Remove algosdk from your dependencies
pip uninstall py-algorand-sdk

# Install the latest algokit-utils (v5 includes all sub-packages)
pip install algokit-utils@latest
```

### Step 2: Update Entry Point

- [ ] If using `get_algod_client()` / `get_indexer_client()`, replace with `AlgorandClient.*`
- [ ] If already using `AlgorandClient`, no changes needed

### Step 3: Update Imports

- [ ] Replace all `from algosdk` imports with equivalent `algokit_*` imports (see [1.4](#14-import-path-migration))
- [ ] Replace `from algokit_utils._legacy_v2` imports
- [ ] Replace `from algokit_utils.beta` imports
- [ ] Update `Arc56Contract` / `Arc32Contract` imports to `algokit_abi`

### Step 4: Update Account Types

- [ ] `SigningAccount` → `AddressWithSigners`
- [ ] `.address` → `.addr` on all account/signer types
- [ ] `TransactionSignerAccountProtocol` → `AddressWithTransactionSigner`
- [ ] `MultiSigAccount` → `MultisigAccount`
- [ ] `MultisigMetadata.addresses` → `.addrs`

### Step 5: Update Transaction Code

- [ ] `OnComplete.NoOpOC` → `OnApplicationComplete.NoOp` (and similar)
- [ ] `SendAtomicTransactionComposerResults` → `SendTransactionComposerResults`
- [ ] `populate_app_call_resources` → `populate_group_resources`
- [ ] Update `TransactionComposer` constructor if using directly

### Step 6: Update App Client Code

- [ ] Replace `ApplicationClient` with `AppClient` / `AppFactory`
- [ ] Replace `ApplicationSpecification` with `Arc56Contract`
- [ ] Update method call patterns to use `app_client.send.call(...)` interface

### Step 7: Update ABI Handling

- [ ] Update code expecting `list[int]` from byte types — now returns `bytes`
- [ ] Update code expecting `int` from `ufixed` types — now returns `decimal.Decimal`
- [ ] Update code expecting `list` from tuple types — now returns `tuple`

### Step 8: Update Direct algosdk Usage

- [ ] Replace `algosdk.v2client.algod.AlgodClient` type annotations with `algokit_algod_client.AlgodClient`
- [ ] Replace `algosdk.v2client.indexer.IndexerClient` with `algokit_indexer_client.IndexerClient`
- [ ] Replace `algosdk.kmd.KMDClient` with `algokit_kmd_client.KmdClient`
- [ ] Update `SuggestedParams` field access: `.gen` → `.genesis_id`, `.gh` → `.genesis_hash`
- [ ] Replace `algosdk.source_map.SourceMap` with `algokit_common.ProgramSourceMap`

### Step 9: Update Model Access Patterns

- [ ] Replace dict-style confirmation access (`["application-index"]`) with attribute access (`.app_id`)
- [ ] Replace dict-style confirmation access (`["asset-index"]`) with attribute access (`.asset_id`)
- [ ] Update block model access for nested header fields (see [7.1](#71-block-model-restructuring))

### Step 10: Verify

- [ ] Run your test suite
- [ ] Check for `ImportError` / `ModuleNotFoundError` (indicates missed import updates)
- [ ] Check for `AttributeError` on `.address` (should be `.addr`)
- [ ] Check for `TypeError` on ABI return values (type changes)
- [ ] Test transaction signing and sending end-to-end
