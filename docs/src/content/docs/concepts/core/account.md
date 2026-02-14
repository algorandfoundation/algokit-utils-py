---
title: "Account Management"
description: "Account management is one of the core capabilities provided by AlgoKit Utils. It allows you to create mnemonic, rekeyed, multisig, transaction signer, idempotent KMD and environment variable injected accounts."
---

Account management is one of the core capabilities provided by AlgoKit Utils. It allows you to create mnemonic, rekeyed, multisig, transaction signer, idempotent KMD and environment variable injected accounts that can be used to sign transactions as well as representing a sender address at the same time. This significantly simplifies management of transaction signing.

## `AccountManager`

The `AccountManager` is a class that is used to get, create, and fund accounts and perform account-related actions such as funding. The `AccountManager` also keeps track of signers for each address so when using the [`TransactionComposer`](../../advanced/transaction-composer) to send transactions, a signer function does not need to manually be specified for each transaction - instead it can be inferred from the sender address automatically!

To get an instance of `AccountManager`, you can use either [`AlgorandClient`](../algorand-client) via `algorand.account` or instantiate it directly:

```python
from algokit_utils import AccountManager

account_manager = AccountManager(client_manager)
```

## `AddressWithTransactionSigner`

The core internal type that holds information about a signer/sender pair for a transaction is `AddressWithTransactionSigner`, which represents a `TransactionSigner` (`signer`) along with a sender address (`addr`) as the encoded string address.

The following conform to `AddressWithTransactionSigner`:

- `AddressWithSigners` - an account that holds a private key and conforms to `AddressWithTransactionSigner`. This was previously named `SigningAccount` in v4.
- `LogicSigAccount` - a wrapper class around logic signature abstractions conforming to `AddressWithTransactionSigner`
- `MultisigAccount` - a wrapper class around multisig abstractions conforming to `AddressWithTransactionSigner`

## Registering a signer

The `AccountManager` keeps track of which signer is associated with a given sender address. This is used by [`AlgorandClient`](../algorand-client) to automatically sign transactions by that sender. Any of the [methods](#accounts) within `AccountManager` that return an account will automatically register the signer with the sender.

There are two methods that can be used for this, `set_signer_from_account`, which takes any number of [account based objects](#underlying-account-classes) that combine signer and sender (`AddressWithSigners` | `LogicSigAccount` | `MultisigAccount`), or `set_signer` which takes the sender address and the `TransactionSigner`:

```python
algorand.account
  .set_signer_from_account(AddressWithSigners(addr=your_address, signer=your_signer))
  .set_signer_from_account(
    LogicSigAccount(logic=program, args=args)
  )
  .set_signer_from_account(
    MultisigAccount(
      MultisigMetadata(
        version=1,
        threshold=1,
        addrs=["ADDRESS1...", "ADDRESS2..."]
      ),
      [account1, account2]
    )
  )
  .set_signer("SENDERADDRESS", transaction_signer)
```

## Default signer

If you want to have a default signer that is used to sign transactions without a registered signer (rather than throwing an exception) then you can use `set_default_signer`:

```python
algorand.account.set_default_signer(my_default_signer)
```

## Get a signer

[`AlgorandClient`](../algorand-client) will automatically retrieve a signer when signing a transaction, but if you need to get a `TransactionSigner` externally to do something more custom then you can use `get_signer` for a given sender address:

```python
signer = algorand.account.get_signer("SENDER_ADDRESS")
```

If there is no signer registered for that sender address it will either return the default signer ([if registered](#default-signer)) or throw an exception.

## Accounts

In order to get/register accounts for signing operations you can use the following methods on [`AccountManager`](#accountmanager) (expressed here as `algorand.account` to denote the syntax via an [`AlgorandClient`](../algorand-client)):

- `from_environment` - Registers and returns an account with private key loaded by convention based on the given name identifier - either by idempotently creating the account in KMD or from environment variable via `process.env['{NAME}_MNEMONIC']` and (optionally) `process.env['{NAME}_SENDER']` (if account is rekeyed)
  - This allows you to have powerful code that will automatically create and fund an account by name locally and when deployed against TestNet/MainNet will automatically resolve from environment variables, without having to have different code
  - Note: `fund_with` allows you to control how many Algo are seeded into an account created in KMD
- `from_mnemonic` - Registers and returns an account with secret key loaded by taking the mnemonic secret
- `multisig` - Registers and returns a multisig account with one or more signing keys loaded
- `rekeyed` - Registers and returns an account representing the given rekeyed sender/signer combination
- `random` - Returns a new, cryptographically randomly generated account with private key loaded
- `from_kmd` - Returns an account with private key loaded from the given KMD wallet (identified by name)
- `logicsig` - Returns an account that represents a logic signature

### Underlying account classes

The following account classes can be used to represent accounts that can sign transactions:

- `AddressWithSigners` - An account that holds a private key and conforms to `AddressWithTransactionSigner`. Supports rekeyed accounts.
- `LogicSigAccount` - An abstraction that supports logic signature signing. Exposes access to the underlying logic signature via `lsig` property.
- `MultisigAccount` - An abstraction that supports multisig accounts with one or more signers present. Exposes access to the underlying multisig via `multisig` property.

### Dispenser

- `dispenser_from_environment` - Returns an account (with private key loaded) that can act as a dispenser from environment variables, or against default LocalNet if no environment variables present
- `localnet_dispenser` - Returns an account with private key loaded that can act as a dispenser for the default LocalNet dispenser account

## Rekey account

One of the unique features of Algorand is the ability to change the private key that can authorise transactions for an account. This is called [rekeying](https://dev.algorand.co/concepts/accounts/rekeying).

> [!WARNING]
> Rekeying should be done with caution as a rekey transaction can result in permanent loss of control of an account.

You can issue a transaction to rekey an account by using the `rekey_account` function:

- `account: str | AddressWithTransactionSigner` - The account address or signing account of the account that will be rekeyed
- `rekeyTo: str | AddressWithTransactionSigner` - The account address or signing account of the account that will be used to authorise transactions for the rekeyed account going forward. If a signing account is provided that will now be tracked as the signer for `account` in the `AccountManager` instance.
- An `options` object, which has:
  - [Common transaction parameters](../algorand-client#transaction-parameters)
  - [Execution parameters](../algorand-client#sending-a-single-transaction)

You can also pass in `rekeyTo` as a [common transaction parameter](../algorand-client#transaction-parameters) to any transaction.

### Examples

```python
# Basic example (with string addresses)
algorand.account.rekey_account(
    account="ACCOUNTADDRESS",
    rekey_to="NEWADDRESS",
)

# Basic example (with signer accounts)
algorand.account.rekey_account(
    account=account1,
    rekey_to=new_signer_account,
)

# Advanced example
algorand.account.rekey_account(
    account="ACCOUNTADDRESS",
    rekey_to="NEWADDRESS",
    lease="lease",
    note="note",
    first_valid_round=1000,
    validity_window=10,
    extra_fee=AlgoAmount.from_micro_algo(1000),
    static_fee=AlgoAmount.from_micro_algo(1000),
    # Max fee doesn't make sense with extra_fee AND static_fee
    # already specified, but here for completeness
    max_fee=AlgoAmount.from_micro_algo(3000),
    max_rounds_to_wait=5,
    suppress_log=True,
)

# Using a rekeyed account
# Note: if a signing account is passed into `algorand.account.rekey_account`
# then you don't need to call `rekeyed_account` to register the new signer
rekeyed_account = algorand.account.rekey_account(account, new_account)
# rekeyed_account can be used to sign transactions on behalf of account...
```

## KMD account management

When running LocalNet, you have an instance of the [Key Management Daemon](https://github.com/algorand/go-algorand/blob/master/daemon/kmd/README.md), which is useful for:

- Accessing the private key of the default accounts that are pre-seeded with Algo so that other accounts can be funded and it's possible to use LocalNet
- Idempotently creating new accounts against a name that will stay intact while the LocalNet instance is running without you needing to store private keys anywhere (i.e. completely automated)

The KMD SDK is fairly low level so to make use of it there is a fair bit of boilerplate code that's needed. This code has been abstracted away into the `KmdAccountManager` class.

To get an instance of the `KmdAccountManager` class you can access it from [`AlgorandClient`](../algorand-client) via `algorand.account.kmd` or instantiate it directly (passing in a [`ClientManager`](../client)):

```python
from algokit_utils import KmdAccountManager

kmd_account_manager = KmdAccountManager(client_manager)
```

The methods that are available are:

- `get_wallet_account` - Returns an Algorand signing account with private key loaded from the given KMD wallet (identified by name).
- `get_or_create_wallet_account` - Gets an account with private key loaded from a KMD wallet of the given name, or alternatively creates one with funds in it via a KMD wallet of the given name.
- `get_localnet_dispenser_account` - Returns an Algorand account with private key loaded for the default LocalNet dispenser account (that can be used to fund other accounts)

```python
# Get a wallet account that seeded the LocalNet network
default_dispenser_account = kmd_account_manager.get_wallet_account(
    "unencrypted-default-wallet",
    lambda a: a["status"] != "Offline" and a["amount"] > 1_000_000_000
)
# Same as above, but dedicated method call for convenience
localnet_dispenser_account = kmd_account_manager.get_localnet_dispenser_account()
# Idempotently get (if exists) or create (if it doesn't exist yet) an account by name using KMD
# if creating it then fund it with 2 ALGO from the default dispenser account
new_account = kmd_account_manager.get_or_create_wallet_account(
  "account1",
  AlgoAmount.from_algo(2)
)
# This will return the same account as above since the name matches
existing_account = kmd_account_manager.get_or_create_wallet_account(
  "account1"
)
```

Some of this functionality is directly exposed from [`AccountManager`](#accountmanager), which has the added benefit of registering the account as a signer so they can be automatically used to sign transactions when using via [`AlgorandClient`](../algorand-client):

```python
# Get and register LocalNet dispenser
localnet_dispenser = algorand.account.localnet_dispenser()
# Get and register a dispenser by environment variable, or if not set then LocalNet dispenser via KMD
dispenser = algorand.account.dispenser_from_environment()
# Get an account from KMD idempotently by name. In this case we'll get the default dispenser account
dispenser_via_kmd = algorand.account.from_kmd('unencrypted-default-wallet', lambda a: a["status"] != 'Offline' and a["amount"] > 1_000_000_000)
# Get / create and register account from KMD idempotently by name
fresh_account_via_kmd = algorand.account.kmd.get_or_create_wallet_account('account1', AlgoAmount.from_algo(2))
```