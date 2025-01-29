# Account management

Account management is one of the core capabilities provided by AlgoKit Utils. It allows you to create mnemonic, rekeyed, multisig, transaction signer, idempotent KMD and environment variable injected accounts that can be used to sign transactions as well as representing a sender address at the same time. This significantly simplifies management of transaction signing.

## `AccountManager`

The [`AccountManager`]() is a class that is used to get, create, and fund accounts and perform account-related actions such as funding. The `AccountManager` also keeps track of signers for each address so when using the [`TransactionComposer`](transaction-composer.md) to send transactions, a signer function does not need to manually be specified for each transaction - instead it can be inferred from the sender address automatically!

To get an instance of `AccountManager`, you can use either [`AlgorandClient`](algorand-client.md) via `algorand.account` or instantiate it directly:

```python
from algokit_utils import AccountManager

account_manager = AccountManager(client_manager)
```

## `TransactionSignerAccountProtocol`

The core internal type that holds information about a signer/sender pair for a transaction is [`TransactionSignerAccountProtocol`](), which represents an `algosdk.transaction.TransactionSigner` (`signer`) along with a sender address (`address`) as the encoded string address.

The following conform to `TransactionSignerAccountProtocol`:

- [`TransactionSignerAccount`]() - a basic transaction signer account that holds an address and a signer conforming to `TransactionSignerAccountProtocol`
- [`SigningAccount`]() - an abstraction that used to be available under `Account` in previous versions of AlgoKit Utils. Renamed for consistency with equivalent `ts` version. Holds private key and conforms to `TransactionSignerAccountProtocol`
- [`LogicSigAccount`]() - a wrapper class around `algosdk` logicsig abstractions conforming to `TransactionSignerAccountProtocol`
- [`MultisigAccount`]() - a wrapper class around `algosdk` multisig abstractions conforming to `TransactionSignerAccountProtocol`

## Registering a signer

The `AccountManager` keeps track of which signer is associated with a given sender address. This is used by [`AlgorandClient`](algorand-client.md) to automatically sign transactions by that sender. Any of the [methods]() within `AccountManager` that return an account will automatically register the signer with the sender.

There are two methods that can be used for this, `set_signer_from_account`, which takes any number of [account based objects]() that combine signer and sender (`TransactionSignerAccount` | `SigningAccount` | `LogicSigAccount` | `MultisigAccount`), or `set_signer` which takes the sender address and the `TransactionSigner`:

```python
algorand.account
  .set_signer_from_account(TransactionSignerAccount(your_address, your_signer))
  .set_signer_from_account(SigningAccount.new_account())
  .set_signer_from_account(
    LogicSigAccount(algosdk.transaction.LogicSigAccount(program, args))
  )
  .set_signer_from_account(
    MultisigAccount(
      MultisigMetadata(
        version = 1,
        threshold = 1,
        addresses = ["ADDRESS1...", "ADDRESS2..."]
      ),
      [account1, account2]
    )
  )
  .set_signer("SENDERADDRESS", transaction_signer)
```

## Default signer

If you want to have a default signer that is used to sign transactions without a registered signer (rather than throwing an exception) then you can [register a default signer]():

```python
algorand.account.set_default_signer(my_default_signer)
```

## Get a signer

[`AlgorandClient`](algorand-client.md) will automatically retrieve a signer when signing a transaction, but if you need to get a `TransactionSigner` externally to do something more custom then you can [retrieve the signer]() for a given sender address:

```python
signer = algorand.account.get_signer("SENDER_ADDRESS")
```

If there is no signer registered for that sender address it will either return the default signer ([if registered]()) or throw an exception.

## Accounts

In order to get/register accounts for signing operations you can use the following methods on [`AccountManager`]() (expressed here as `algorand.account` to denote the syntax via an [`AlgorandClient`](algorand-client.md)):

- [`algorand.account.from_environment(name, fund_with)`]() - Registers and returns an account with private key loaded by convention based on the given name identifier - either by idempotently creating the account in KMD or from environment variable via `process.env['{NAME}_MNEMONIC']` and (optionally) `process.env['{NAME}_SENDER']` (if account is rekeyed)
  - This allows you to have powerful code that will automatically create and fund an account by name locally and when deployed against TestNet/MainNet will automatically resolve from environment variables, without having to have different code
  - Note: `fund_with` allows you to control how many Algo are seeded into an account created in KMD
- [`algorand.account.from_mnemonic(mnemonic_secret, sender?)`]() - Registers and returns an account with secret key loaded by taking the mnemonic secret
- [`algorand.account.multisig(multisig_params, signing_accounts)`]() - Registers and returns a multisig account with one or more signing keys loaded
- [`algorand.account.rekeyed(sender, signer)`]() - Registers and returns an account representing the given rekeyed sender/signer combination
- [`algorand.account.random()`]() - Returns a new, cryptographically randomly generated account with private key loaded
- [`algorand.account.from_kmd()`]() - Returns an account with private key loaded from the given KMD wallet (identified by name)
- [`algorand.account.logicsig(program, args?)`]() - Returns an account that represents a logic signature

### Underlying account classes

While `TransactionSignerAccount` is the main class used to represent an account that can sign, there are underlying account classes that can underpin the signer within the transaction signer account.

- `Account` - An in-built `algosdk.Account` object that has an address and private signing key, this can be created
- [`SigningAccount`]() - An abstraction around `algosdk.Account` that supports rekeyed accounts
- `LogicSigAccount` - An in-built algosdk `algosdk.LogicSigAccount` object
- [`MultisigAccount`]() - An abstraction around `algosdk.MultisigMetadata`, `algosdk.makeMultiSigAccountTransactionSigner`, `algosdk.multisigAddress`, `algosdk.signMultisigTransaction` and `algosdk.appendSignMultisigTransaction` that supports multisig accounts with one or more signers present

### Dispenser

- [`algorand.account.dispenserFromEnvironment()`]() - Returns an account (with private key loaded) that can act as a dispenser from environment variables, or against default LocalNet if no environment variables present
- [`algorand.account.localNetDispenser()`]() - Returns an account with private key loaded that can act as a dispenser for the default LocalNet dispenser account

## Rekey account

One of the unique features of Algorand is the ability to change the private key that can authorise transactions for an account. This is called [rekeying](https://developer.algorand.org/docs/get-details/accounts/rekey/).

> [!WARNING]
> Rekeying should be done with caution as a rekey transaction can result in permanent loss of control of an account.

You can issue a transaction to rekey an account by using the [`algorand.account.rekeyAccount(account, rekeyTo, options)`]() function:

- `account: string | TransactionSignerAccount` - The account address or signing account of the account that will be rekeyed
- `rekeyTo: string | TransactionSignerAccount` - The account address or signing account of the account that will be used to authorise transactions for the rekeyed account going forward. If a signing account is provided that will now be tracked as the signer for `account` in the `AccountManager` instance.
- An `options` object, which has:
  - [Common transaction parameters](algorand-client.md#transaction-parameters)
  - [Execution parameters](algorand-client.md#sending-a-single-transaction)

You can also pass in `rekeyTo` as a [common transaction parameter](algorand-client.md#transaction-parameters) to any transaction.

### Examples

```python
# Basic example (with string addresses)

algorand.account.rekey_account({
  account: "ACCOUNTADDRESS",
  rekey_to: "NEWADDRESS",
})

# Basic example (with signer accounts)

algorand.account.rekey_account({
  account: account1,
  rekey_to: new_signer_account,
})

# Advanced example

algorand.account.rekey_account({
  account: "ACCOUNTADDRESS",
  rekey_to: "NEWADDRESS",
  lease: "lease",
  note: "note",
  first_valid_round: 1000,
  validity_window: 10,
  extra_fee: AlgoAmount.from_micro_algos(1000),
  static_fee: AlgoAmount.from_micro_algos(1000),
  # Max fee doesn't make sense with extra_fee AND static_fee
  #  already specified, but here for completeness
  max_fee: AlgoAmount.from_micro_algos(3000),
  max_rounds_to_wait_for_confirmation: 5,
  suppress_log: True,
})


# Using a rekeyed account

Note: if a signing account is passed into `algorand.account.rekey_account` then you don't need to call `rekeyed_account` to register the new signer

rekeyed_account = algorand.account.rekey_account(account, new_account)
# rekeyed_account can be used to sign transactions on behalf of account...
```

## KMD account management

When running LocalNet, you have an instance of the [Key Management Daemon](https://github.com/algorand/go-algorand/blob/master/daemon/kmd/README.md), which is useful for:

- Accessing the private key of the default accounts that are pre-seeded with Algo so that other accounts can be funded and it’s possible to use LocalNet
- Idempotently creating new accounts against a name that will stay intact while the LocalNet instance is running without you needing to store private keys anywhere (i.e. completely automated)

The KMD SDK is fairly low level so to make use of it there is a fair bit of boilerplate code that’s needed. This code has been abstracted away into the `KmdAccountManager` class.

To get an instance of the `KmdAccountManager` class you can access it from [`AlgorandClient`](algorand-client.md) via `algorand.account.kmd` or instantiate it directly (passing in a [`ClientManager`](client.md)):

```python
from algokit_utils import KmdAccountManager

kmd_account_manager = KmdAccountManager(client_manager)
```

The methods that are available are:

- [`get_wallet_account(wallet_name, predicate?, sender?)`]()\` - Returns an Algorand signing account with private key loaded from the given KMD wallet (identified by name).
- [`get_or_create_wallet_account(name, fund_with?)`]()\` - Gets an account with private key loaded from a KMD wallet of the given name, or alternatively creates one with funds in it via a KMD wallet of the given name.
- [`get_localnet_dispenser_account()`]()\` - Returns an Algorand account with private key loaded for the default LocalNet dispenser account (that can be used to fund other accounts)

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
  AlgoAmount.from_algos(2)
)
# This will return the same account as above since the name matches
existing_account = kmd_account_manager.get_or_create_wallet_account(
  "account1"
)
```

Some of this functionality is directly exposed from [`AccountManager`](), which has the added benefit of registering the account as a signer so they can be automatically used to sign transactions when using via [`AlgorandClient`](algorand-client.md):

```python
# Get and register LocalNet dispenser
localnet_dispenser = algorand.account.localnet_dispenser()
# Get and register a dispenser by environment variable, or if not set then LocalNet dispenser via KMD
dispenser = algorand.account.dispenser_from_environment()
# Get / create and register account from KMD idempotently by name
account1 = algorand.account.from_kmd("account1", AlgoAmount.from_algos(2))
```
