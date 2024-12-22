# Account management

Account management is one of the core capabilities provided by AlgoKit Utils. It allows you to create mnemonic, rekeyed, multisig, transaction signer, idempotent KMD and environment variable injected accounts that can be used to sign transactions as well as representing a sender address at the same time. This significantly simplifies management of transaction signing.

## `AccountManager`

The `AccountManager` is a class that is used to get, create, and fund accounts and perform account-related actions such as funding. The `AccountManager` also keeps track of signers for each address so when using transaction composition to send transactions, a signer function does not need to manually be specified for each transaction - instead it can be inferred from the sender address automatically!

To get an instance of `AccountManager`, you can use either use the `AlgorandClient` via `algorand.account` or instantiate it directly:

```python
from algokit_utils import AccountManager

account_manager = AccountManager(client_manager)
```

## `Account` and Transaction Signing

The core type that holds information about an account is the `Account` class, which is a thin wrapper on top of stateless account address generation methods from `py-algorand-sdk`. It encapsulates a private key and address, with convenience properties for `address`, `signer` and `public_key`. The `signer` property returns an `AccountTransactionSigner` which ties together the address and signing capability.

This is different from the TypeScript implementation which uses a type called `Account` that represents an `algosdk.atomic_transaction_composer.TransactionSigner` (`signer`) along with a sender address (`addr`) as the encoded string address.

## Registering a signer

The `AccountManager` keeps track of which signer is associated with a given sender address. This is used to automatically sign transactions by that sender. Any of the [methods](#accounts) within `AccountManager` that return an account will automatically register the signer with the sender. If however, you are creating a signer external to the `AccountManager`, then you need to register the signer with the `AccountManager` if you want it to be able to automatically sign transactions from that sender.

There are two methods that can be used for this, `set_signer_from_account`, which takes any number of account based objects that combine signer and sender (`Account` | `Account` | `LogicSigAccount` | `SigningAccount` | `MultisigAccount`), or `set_signer` which takes the sender address and the `TransactionSigner`:

```python
account_manager.set_signer_from_account(Account(address=..., private_key=...))
account_manager.set_signer_from_account(LogicSigAccount(program, args))
account_manager.set_signer_from_account(SigningAccount(mnemonic, sender))
account_manager.set_signer_from_account(MultiSigAccount(multisig_params, [account1, account2]))
account_manager.set_signer("SENDERADDRESS", transaction_signer)
```

## Default signer

If you want to have a default signer that is used to sign transactions without a registered signer (rather than throwing an exception) then you can register a default signer:

```python
account_manager.set_default_signer(my_default_signer)
```

## Get a signer

The library will automatically retrieve a signer when signing a transaction, but if you need to get a `TransactionSigner` externally to do something more custom then you can retrieve the signer for a given sender address:

```python
signer = account_manager.get_signer("SENDER_ADDRESS")
```

If there is no signer registered for that sender address it will either return the default signer (if registered) or raise an exception.

## Accounts

In order to get/register accounts for signing operations you can use the following methods on `AccountManager`:

- `account_manager.from_environment(name, fund_with)` - Registers and returns an account with private key loaded by convention based on the given name identifier - either by idempotently creating the account in KMD or from environment variable via `{NAME}_MNEMONIC` and (optionally) `{NAME}_SENDER` (if account is rekeyed)
  - This allows you to have powerful code that will automatically create and fund an account by name locally and when deployed against TestNet/MainNet will automatically resolve from environment variables, without having to have different code
  - Note: `fund_with` allows you to control how many Algo are seeded into an account created in KMD
- `account_manager.from_mnemonic(mnemonic_secret, sender=None)` - Registers and returns an account with secret key loaded by taking the mnemonic secret
- `account_manager.multisig(multisig_params, signing_accounts)` - Registers and returns a multisig account with one or more signing keys loaded
- `account_manager.rekeyed(sender, signer)` - Registers and returns an account representing the given rekeyed sender/signer combination
- `account_manager.random()` - Returns a new, cryptographically randomly generated account with private key loaded
- `account_manager.from_kmd()` - Returns an account with private key loaded from the given KMD wallet (identified by name)
- `account_manager.logicsig(program, args=None)` - Returns an account that represents a logic signature

### Underlying account classes

While `Account` is the main class used to represent an account that can sign, there are underlying account classes that can underpin the signer within the transaction signer account.

- `TransactionSigner` - an in-built `algosdk.atomic_transaction_composer.TransactionSigner` object that can sign transactions.
- `LogicSigAccount` - An in-built algosdk `LogicSigAccount` object for logic signature accounts
- `MultisigAccount` - An abstraction around multisig accounts that supports multisig accounts with one or more signers present

### Dispenser

- `account_manager.dispenser_from_environment()` - Returns an account (with private key loaded) that can act as a dispenser from environment variables, or against default LocalNet if no environment variables present
- `account_manager.local_net_dispenser()` - Returns an account with private key loaded that can act as a dispenser for the default LocalNet dispenser account

## Rekey account

One of the unique features of Algorand is the ability to change the private key that can authorise transactions for an account. This is called [rekeying](https://developer.algorand.org/docs/get-details/accounts/rekey/).

```{warning}
Rekeying should be done with caution as a rekey transaction can result in permanent loss of control of an account.
```

You can issue a transaction to rekey an account by using the `account_manager.rekey_account(account, rekey_to, **options)` function:

- `account: str | Account` - The account address or signing account of the account that will be rekeyed
- `rekey_to: str | Account` - The account address or signing account of the account that will be used to authorise transactions for the rekeyed account going forward. If a signing account is provided that will now be tracked as the signer for `account` in the `AccountManager` instance.
- `options` - A set of keyword arguments of optional parameters, which includes:
  - Common transaction parameters
  - Execution parameters

You can also pass in `rekey_to` as a common transaction parameter to any transaction.

### Examples

```python
# Basic example (with string addresses)
account_manager.rekey_account(account="ACCOUNTADDRESS", rekey_to="NEWADDRESS")

# Basic example (with signer accounts)
account_manager.rekey_account(account=account1, rekey_to=new_signer_account)

# Advanced example
account_manager.rekey_account(
    account="ACCOUNTADDRESS",
    rekey_to="NEWADDRESS",
    lease="lease",
    note="note",
    first_valid_round=1000,
    validity_window=10,
    extra_fee=1000,  # microAlgos
    static_fee=1000,  # microAlgos
    max_fee=3000,  # microAlgos
    max_rounds_to_wait_for_confirmation=5,
    suppress_log=True,
)

# Using a rekeyed account
# Note: if a signing account is passed into account_manager.rekey_account then you don't need to call rekeyed_account to register the new signer
rekeyed_account = account_manager.rekeyed(account, new_account)
# rekeyed_account can be used to sign transactions on behalf of account...
```

# KMD account management

When running LocalNet, you have an instance of the [Key Management Daemon](https://github.com/algorand/go-algorand/blob/master/daemon/kmd/README.md), which is useful for:

- Accessing the private key of the default accounts that are pre-seeded with Algo so that other accounts can be funded and it's possible to use LocalNet
- Idempotently creating new accounts against a name that will stay intact while the LocalNet instance is running without you needing to store private keys anywhere (i.e. completely automated)

The KMD SDK is fairly low level so to make use of it there is a fair bit of boilerplate code that's needed. This code has been abstracted away into the `KmdAccountManager` class.

To get an instance of the `KmdAccountManager` class you can access it from `AccountManager` via `account_manager.kmd` or instantiate it directly (passing in a `ClientManager`):

```python
from algokit_utils import KmdAccountManager

# Algod client only
kmd_account_manager = KmdAccountManager(client_manager)
```

The methods that are available are:

- `get_wallet_account(wallet_name, predicate=None, sender=None)` - Returns an Algorand signing account with private key loaded from the given KMD wallet (identified by name).
- `get_or_create_wallet_account(name, fund_with=None)` - Gets an account with private key loaded from a KMD wallet of the given name, or alternatively creates one with funds in it via a KMD wallet of the given name.
- `get_local_net_dispenser_account()` - Returns an Algorand account with private key loaded for the default LocalNet dispenser account (that can be used to fund other accounts)

```python
# Get a wallet account that seeded the LocalNet network
default_dispenser_account = kmd_account_manager.get_wallet_account(
    "unencrypted-default-wallet",
    lambda a: a.status != "Offline" and a.amount > 1_000_000_000,
)
# Same as above, but dedicated method call for convenience
local_net_dispenser_account = kmd_account_manager.get_local_net_dispenser_account()
# Idempotently get (if exists) or create (if it doesn't exist yet) an account by name using KMD
# if creating it then fund it with 2 ALGO from the default dispenser account
new_account = kmd_account_manager.get_or_create_wallet_account("account1", 2_000_000)  # microAlgos
# This will return the same account as above since the name matches
existing_account = kmd_account_manager.get_or_create_wallet_account("account1")
```

Some of this functionality is directly exposed from `AccountManager`, which has the added benefit of registering the account as a signer so they can be automatically used to sign transactions:

```python
# Get and register LocalNet dispenser
local_net_dispenser = account_manager.local_net_dispenser()
# Get and register a dispenser by environment variable, or if not set then LocalNet dispenser via KMD
dispenser = account_manager.dispenser_from_environment()
# Get / create and register account from KMD idempotently by name
account1 = account_manager.from_kmd("account1", 2_000_000)  # microAlgos
```
