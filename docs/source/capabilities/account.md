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

The core type that holds information about a signer/sender pair for a transaction in Python is the `Account` class, which represents both the signing capability and sender address in one object. This is different from the TypeScript implementation which uses `TransactionSignerAccount` interface that combines an `algosdk.TransactionSigner` with a sender address.

The Python `Account` class provides:

- `address` - The encoded string address
- `private_key` - The private key for signing
- `signer` - An `AccountTransactionSigner` that can sign transactions
- `public_key` - The public key associated with this account

## Registering a signer

The `AccountManager` keeps track of which signer is associated with a given sender address. This is used by the transaction composition functionality to automatically sign transactions by that sender. Any of the [methods](#accounts) within `AccountManager` that return an account will automatically register the signer with the sender.

There are two methods that can be used for this:

```python
# Register an account object that has both signer and sender
account_manager.set_signer_from_account(account)

# Register just a signer for a given sender address
account_manager.set_signer("SENDER_ADDRESS", transaction_signer)
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

- `from_environment(name: str, fund_with: AlgoAmount | None = None) -> Account` - Registers and returns an account with private key loaded by convention based on the given name identifier - either by idempotently creating the account in KMD or from environment variable via `{NAME}_MNEMONIC` and (optionally) `{NAME}_SENDER` (if account is rekeyed)
  - This allows you to have powerful code that will automatically create and fund an account by name locally and when deployed against TestNet/MainNet will automatically resolve from environment variables, without having to have different code
  - Note: `fund_with` allows you to control how many Algo are seeded into an account created in KMD
- `from_mnemonic(mnemonic_secret: str) -> Account` - Registers and returns an account with secret key loaded by taking the mnemonic secret
- `multisig(version: int, threshold: int, addrs: list[str], signing_accounts: list[Account]) -> MultisigAccount` - Registers and returns a multisig account with one or more signing keys loaded
- `rekeyed(sender: Account | str, account: Account) -> Account` - Registers and returns an account representing the given rekeyed sender/signer combination
- `random() -> Account` - Returns a new, cryptographically randomly generated account with private key loaded
- `from_kmd(name: str, predicate: Callable[[dict[str, Any]], bool] | None = None, sender: str | None = None) -> Account` - Returns an account with private key loaded from the given KMD wallet
- `logic_sig(program: bytes, args: list[bytes] | None = None) -> LogicSigAccount` - Returns an account that represents a logic signature

### Underlying account classes

While `Account` is the main class used to represent an account that can sign, there are underlying account classes that can underpin the signer:

- `Account` - The main account class that combines address and private key
- `LogicSigAccount` - An in-built algosdk `LogicSigAccount` object for logic signature accounts
- `MultisigAccount` - An abstraction around multisig accounts that supports multisig accounts with one or more signers present

### Dispenser

- `dispenser_from_environment() -> Account` - Returns an account (with private key loaded) that can act as a dispenser from environment variables, or against default LocalNet if no environment variables present
- `local_net_dispenser() -> Account` - Returns an account with private key loaded that can act as a dispenser for the default LocalNet dispenser account

## Rekey account

One of the unique features of Algorand is the ability to change the private key that can authorise transactions for an account. This is called [rekeying](https://developer.algorand.org/docs/get-details/accounts/rekey/).

```{warning}
Rekeying should be done with caution as a rekey transaction can result in permanent loss of control of an account.
```

You can issue a transaction to rekey an account by using the `rekey_account` method:

```python
account_manager.rekey_account(
    account="ACCOUNTADDRESS",  # str | Account
    rekey_to="NEWADDRESS",    # str | Account
    # Optional parameters
    signer=None,              # TransactionSigner
    note=None,               # bytes
    lease=None,              # bytes
    static_fee=None,         # AlgoAmount
    extra_fee=None,          # AlgoAmount
    max_fee=None,            # AlgoAmount
    validity_window=None,    # int
    first_valid_round=None,  # int
    last_valid_round=None,   # int
    suppress_log=None        # bool
)
```

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

- `get_wallet_account(wallet_name: str, predicate: Callable[[dict[str, Any]], bool] | None = None, sender: str | None = None) -> Account` - Returns an Algorand signing account with private key loaded from the given KMD wallet (identified by name).
- `get_or_create_wallet_account(name: str, fund_with: AlgoAmount | None = None) -> Account` - Gets an account with private key loaded from a KMD wallet of the given name, or alternatively creates one with funds in it via a KMD wallet of the given name.
- `get_local_net_dispenser_account() -> Account` - Returns an Algorand account with private key loaded for the default LocalNet dispenser account (that can be used to fund other accounts)

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
new_account = kmd_account_manager.get_or_create_wallet_account("account1", AlgoAmount.from_algo(2))
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
account1 = account_manager.from_kmd("account1", AlgoAmount.from_algo(2))
```
