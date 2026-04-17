# AlgoKit Utils Python Examples

Runnable code examples demonstrating every major feature of the `algokit-utils` Python library.

## Overview

This folder contains 109 self-contained examples organized into 8 categories. Each example is a standalone Python file that demonstrates specific functionality, progressing from basic to advanced usage within each category.

## Prerequisites

- Python >= 3.12
- [AlgoKit LocalNet](https://github.com/algorandfoundation/algokit-cli) running (for network examples)

Some examples (marked "No LocalNet required") work with pure utility functions and don't need a running network.

## Quick Start

All commands are run from the `examples/` directory:

```bash
cd examples

# Install dependencies (resolves algokit-utils from parent directory)
uv sync

# Run a single example
uv run python transact/01_payment_transaction.py

# Run all examples in a category
./transact/verify-all.sh

# Run all examples
./verify-all.sh
```

## Examples by Package

### ABI (`abi/`)

ABI type parsing, encoding, and decoding following the ARC-4 specification.

| File                            | Description                                                           |
| ------------------------------- | --------------------------------------------------------------------- |
| `01_type_parsing.py`            | Parse ABI type strings into type objects with `ABIType.from_string()` |
| `02_primitive_types.py`         | Encode/decode uint, bool, and byte types                              |
| `03_address_type.py`            | Encode/decode Algorand addresses (32-byte public keys)                |
| `04_string_type.py`             | Encode/decode dynamic strings with length prefix                      |
| `05_static_array.py`            | Fixed-length arrays like `byte[32]` and `uint64[3]`                   |
| `06_dynamic_array.py`           | Variable-length arrays with head/tail encoding                        |
| `07_tuple_type.py`              | Encode/decode tuples with mixed types                                 |
| `08_struct_type.py`             | Named structs with field metadata                                     |
| `09_struct_tuple_conversion.py` | Convert between struct objects and tuple arrays                       |
| `10_bool_packing.py`            | Efficient bool array packing (8 bools per byte)                       |
| `11_abi_method.py`              | Parse method signatures and compute 4-byte selectors                  |
| `12_avm_types.py`               | AVM-specific types (AVMBytes, AVMString, AVMUint64)                   |
| `13_type_guards.py`             | Type guard functions for argument/type categorization                 |
| `14_complex_nested.py`          | Deeply nested types combining arrays, tuples, structs                 |
| `15_arc56_storage.py`           | ARC-56 storage helpers for contract state inspection                  |

### Algo25 (`algo25/`)

Mnemonic and seed conversion utilities following the Algorand 25-word mnemonic standard. No LocalNet required.

| File                           | Description                                         |
| ------------------------------ | --------------------------------------------------- |
| `01_mnemonic_from_seed.py`     | Convert 32-byte seed to 25-word mnemonic            |
| `02_seed_from_mnemonic.py`     | Convert 25-word mnemonic back to 32-byte seed       |
| `03_secret_key_to_mnemonic.py` | Convert 64-byte secret key to mnemonic              |
| `04_master_derivation_key.py`  | MDK alias functions for wallet derivation workflows |
| `05_error_handling.py`         | Handle invalid words, checksums, and seed lengths   |

### Algod Client (`algod_client/`)

Algorand node operations and queries using the AlgodClient.

| File                         | Description                                                    |
| ---------------------------- | -------------------------------------------------------------- |
| `01_node_health_status.py`   | Check node health with `health_check()`, `ready()`, `status()` |
| `02_version_genesis.py`      | Get node version and genesis configuration                     |
| `03_ledger_supply.py`        | Query total, online, and circulating supply                    |
| `04_account_info.py`         | Get account balances, assets, and application state            |
| `05_transaction_params.py`   | Get suggested params for transaction construction              |
| `06_send_transaction.py`     | Submit transactions and wait for confirmation                  |
| `07_pending_transactions.py` | Query pending transactions in the mempool                      |
| `08_block_data.py`           | Retrieve block info, hash, and transaction IDs                 |
| `09_asset_info.py`           | Get asset parameters by ID                                     |
| `10_application_info.py`     | Get application state and parameters by ID                     |
| `11_application_boxes.py`    | Query application box storage                                  |
| `12_teal_compile.py`         | Compile TEAL source and disassemble bytecode                   |
| `13_simulation.py`           | Simulate transactions before submitting                        |
| `14_state_deltas.py`         | Get ledger state changes for rounds/transactions               |
| `15_transaction_proof.py`    | Get Merkle proofs for transaction inclusion                    |
| `16_lightblock_proof.py`     | Get light block header proofs for state verification           |
| `17_state_proof.py`          | Get cryptographic state proofs for cross-chain verification    |
| `18_devmode_timestamp.py`    | Control block timestamps in DevMode                            |
| `19_sync_round.py`           | Manage node sync round for storage optimization                |

### Algorand Client (`algorand_client/`)

High-level AlgorandClient API for simplified blockchain interactions.

| File                         | Description                                                                                                     |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `01_client_instantiation.py` | Create AlgorandClient via `default_localnet()`, `testnet()`, `mainnet()`, `from_environment()`, `from_config()` |
| `02_algo_amount.py`          | AlgoAmount utility for safe ALGO/microALGO arithmetic and formatting                                            |
| `03_signer_config.py`        | Configure transaction signers with `set_default_signer()`, `set_signer_from_account()`, `set_signer()`          |
| `04_params_config.py`        | Configure suggested params: validity window, caching, cache timeout                                             |
| `05_account_manager.py`      | Create/import accounts: random, mnemonic, KMD, multisig, logicsig, rekeyed                                      |
| `06_send_payment.py`         | Send ALGO payments with amount, note, and close_remainder_to                                                    |
| `07_send_asset_ops.py`       | ASA operations: create, config, opt-in, transfer, freeze, clawback, destroy                                     |
| `08_send_app_ops.py`         | Application operations: create, update, call, opt-in, close-out, delete                                         |
| `09_create_transaction.py`   | Create unsigned transactions for inspection and custom signing workflows                                        |
| `10_transaction_composer.py` | Build atomic transaction groups with `new_group()`, `simulate()`, `send()`                                      |
| `11_asset_manager.py`        | Query assets and perform bulk opt-in/opt-out operations                                                         |
| `12_app_manager.py`          | Query app info, global/local state, box storage, compile TEAL                                                   |
| `13_app_deployer.py`         | Idempotent app deployment with update/replace strategies                                                        |
| `14_client_manager.py`       | Access raw algod/indexer/kmd clients and typed app clients                                                      |
| `15_error_transformers.py`   | Register custom error transformers for enhanced debugging                                                       |

### Common (`common/`)

Utility functions and helpers. No LocalNet required.

| File                     | Description                                            |
| ------------------------ | ------------------------------------------------------ |
| `01_address_basics.py`   | Parse, validate, and compare addresses                 |
| `02_address_encoding.py` | Encode/decode addresses, compute application addresses |
| `03_array_utilities.py`  | Compare and concatenate byte arrays                    |
| `04_constants.py`        | Protocol constants (limits, sizes, separators)         |
| `05_crypto_hash.py`      | SHA-512/256 hashing for transaction IDs and checksums  |
| `06_logger.py`           | Logger interface for consistent SDK logging            |
| `07_json_bigint.py`      | Parse/stringify JSON with large integer support        |
| `08_msgpack.py`          | MessagePack encoding for transaction serialization     |
| `09_primitive_codecs.py` | Codecs for numbers, strings, bytes, addresses          |
| `10_composite_codecs.py` | Array, Map, and Record codecs                          |
| `11_model_codecs.py`     | Object model codecs with field metadata                |
| `12_sourcemap.py`        | Map TEAL program counters to source locations          |

### Indexer Client (`indexer_client/`)

Blockchain data queries using the IndexerClient.

| File                         | Description                                     |
| ---------------------------- | ----------------------------------------------- |
| `01_health_check.py`         | Check indexer health status                     |
| `02_account_lookup.py`       | Lookup and search accounts                      |
| `03_account_assets.py`       | Query account asset holdings and created assets |
| `04_account_applications.py` | Query account app relationships and local state |
| `05_account_transactions.py` | Get account transaction history                 |
| `06_transaction_lookup.py`   | Lookup single transaction by ID                 |
| `07_transaction_search.py`   | Search transactions with filters                |
| `08_asset_lookup.py`         | Lookup and search assets                        |
| `09_asset_balances.py`       | Get all holders of an asset                     |
| `10_asset_transactions.py`   | Get transactions for a specific asset           |
| `11_application_lookup.py`   | Lookup and search applications                  |
| `12_application_logs.py`     | Query application log emissions                 |
| `13_application_boxes.py`    | Search application box storage                  |
| `14_block_lookup.py`         | Lookup block information                        |
| `15_block_headers.py`        | Search block headers                            |
| `16_pagination.py`           | Handle pagination with limit/next parameters    |

### KMD Client (`kmd_client/`)

Key Management Daemon operations for wallet and key management.

| File                             | Description                                        |
| -------------------------------- | -------------------------------------------------- |
| `01_version.py`                  | Get KMD server version information                 |
| `02_wallet_management.py`        | Create, list, rename, and get wallet info          |
| `03_wallet_sessions.py`          | Manage wallet handle tokens (init, renew, release) |
| `04_key_generation.py`           | Generate deterministic keys in a wallet            |
| `05_key_import_export.py`        | Import external keys and export private keys       |
| `06_key_listing_deletion.py`     | List and delete keys from a wallet                 |
| `07_master_key_export.py`        | Export master derivation key for backup            |
| `08_multisig_setup.py`           | Create multisig accounts with M-of-N threshold     |
| `09_multisig_management.py`      | List, export, and delete multisig accounts         |
| `10_transaction_signing.py`      | Sign transactions using wallet keys                |
| `11_multisig_signing.py`         | Sign multisig transactions (partial + complete)    |
| `12_program_signing.py`          | Create delegated logic signatures                  |
| `13_multisig_program_signing.py` | Create delegated multisig logic signatures         |

### Signing (`signing/`)

Secure secret management and external KMS signing for production-grade security.

| File                         | Description                                                    |
| ---------------------------- | -------------------------------------------------------------- |
| `01_ed25519_from_keyring.py` | Store and sign with Ed25519 seed from OS keyring               |
| `02_hd_from_keyring.py`      | Store and sign with HD extended private key from keyring       |
| `03_aws_kms.py`              | Sign transactions using AWS KMS (with mock client for testing) |

### Transact (`transact/`)

Low-level transaction construction and signing.

| File                        | Description                                      |
| --------------------------- | ------------------------------------------------ |
| `01_payment_transaction.py` | Send ALGO between accounts                       |
| `02_payment_close.py`       | Close account by transferring all remaining ALGO |
| `03_asset_create.py`        | Create Algorand Standard Assets (ASA)            |
| `04_asset_transfer.py`      | Opt-in and transfer assets between accounts      |
| `05_asset_freeze.py`        | Freeze and unfreeze asset holdings               |
| `06_asset_clawback.py`      | Clawback assets using clawback address           |
| `07_atomic_group.py`        | Group transactions atomically (all-or-nothing)   |
| `08_atomic_swap.py`         | Swap ALGO for ASA between two parties            |
| `09_single_sig.py`          | Create ed25519 keypairs and sign transactions    |
| `10_multisig.py`            | Create and use 2-of-3 multisig accounts          |
| `11_logic_sig.py`           | Use logic signatures to authorize transactions   |
| `12_fee_calculation.py`     | Estimate size and calculate transaction fees     |
| `13_encoding_decoding.py`   | Serialize/deserialize transactions to msgpack    |
| `14_app_call.py`            | Deploy and interact with smart contracts         |

## Shared Utilities

The `shared/` directory contains common utilities:

- **`utils.py`** - Helper functions for client creation, account management, formatting, and common operations
- **`constants.py`** - LocalNet configuration (servers, ports, tokens)
- **`artifacts/`** - TEAL smart contract files for testing

## Development

### Adding New Examples

1. Create a file following naming: `NN_descriptive_name.py`
2. Add a docstring header describing the example
3. Add to the category's `verify-all.sh` script

### Example Header Format

```python
"""
Example: [Title]

This example demonstrates [description].
- Key operation 1
- Key operation 2

Prerequisites:
- LocalNet running (or "No LocalNet required")
"""
```

### Running Tests

```bash
# Run all verification scripts (from examples/)
./verify-all.sh
```

## License

MIT - see [LICENSE](../LICENSE) for details.
