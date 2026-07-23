---
title: "Account management"
description: "Account management is one of the core capabilities provided by AlgoKit Utils. It allows you to create mnemonic, rekeyed, multisig, transaction signer, idempotent KMD and environment variable injected accounts that can be used to sign transactions as well as representing a sender address at the same time. This significantly simplifies management of transaction signing."
tableOfContents:
  minHeadingLevel: 2
  maxHeadingLevel: 2
---

Account management is one of the core capabilities provided by AlgoKit Utils. It allows you to create mnemonic, rekeyed, multisig, transaction signer, idempotent KMD and environment variable injected accounts that can be used to sign transactions as well as representing a sender address at the same time. This significantly simplifies management of transaction signing.

> [!NOTE]
> This page documents the AlgoKit Utils (Python) code for working with accounts. For the underlying concepts — account types, keys and addresses, rekeying, multisig — see the account guides on the [Algorand Developer Portal](https://dev.algorand.co/concepts/accounts/overview).

### `AccountManager`

The `AccountManager` is a class that is used to get, create, and fund accounts and perform account-related actions such as funding. The `AccountManager` also keeps track of signers for each address so when using the [`TransactionComposer`](../../advanced/transaction-composer/) to send transactions, a signer function does not need to manually be specified for each transaction - instead it can be inferred from the sender address automatically!

To get an instance of `AccountManager`, you can use either [`AlgorandClient`](../algorand-client/) via `algorand.account` or instantiate it directly:

```python
from algokit_utils import AccountManager

account_manager = AccountManager(client_manager)
```

## Create Accounts

In order to get/register accounts for signing operations you can use the following methods on [`AccountManager`](#accountmanager) (expressed here as `algorand.account` to denote the syntax via an [`AlgorandClient`](../algorand-client/)):

- `from_environment` - Registers and returns an account with private key loaded by convention based on the given name identifier - either by idempotently creating the account in KMD or from environment variable via `process.env['{NAME}_MNEMONIC']` and (optionally) `process.env['{NAME}_SENDER']` (if account is rekeyed)
  - This allows you to have powerful code that will automatically create and fund an account by name locally and when deployed against TestNet/MainNet will automatically resolve from environment variables, without having to have different code
  - Note: `fund_with` allows you to control how many Algo are seeded into an account created in KMD
- `from_mnemonic` - Registers and returns an account with secret key loaded by taking the mnemonic secret
- `multisig` - Registers and returns a multisig account with one or more signing keys loaded
- `rekeyed` - Registers and returns an account representing the given rekeyed sender/signer combination
- `random` - Returns a new, cryptographically randomly generated account with private key loaded
- `from_kmd` - Returns an account with private key loaded from the given KMD wallet (identified by name)
- `logicsig` - Returns an account that represents a logic signature

> [!NOTE]
> For the concept behind standalone, KMD-managed and logic signature accounts, see [Creating an account](https://dev.algorand.co/concepts/accounts/create).

### Random account generation

Generate a new, cryptographically random account. Each account has a freshly generated private/public key pair.

```python
random_account = algorand.account.random()
```

### Mnemonic-based account recovery

Create an account from an existing 25-word mnemonic phrase, allowing account recovery and reuse of predefined test accounts.

```python
mnemonic_account = algorand.account.from_mnemonic(mnemonic="MNEMONIC_PHRASE")
```

### KMD client based account creation

Get or create an account from LocalNet's KMD (Key Management Daemon) by name. If the account doesn't exist, it will be created.

```python
kmd_account = algorand.account.from_kmd(name="ACCOUNT_NAME")
```

Other operations, such as creating and renaming a wallet, can also be performed via the KMD client.

```python
# Create a wallet with the KMD client
algorand.client.kmd.create_wallet(name="ACCOUNT_NAME", pswd="password")

# Rename a wallet with the KMD client
algorand.client.kmd.rename_wallet(
    id="PX2KLH4IVQ25DIU2IVGDWRPJ66RJKOCJ6F7CBCBQA4IXL2GAX645WSG3IQ",
    password="new_password",
    new_name="NEW_ACCOUNT_NAME",
)
```

### Environment variable based account creation

Get or create an account from environment variables. When running against LocalNet, this will create a funded wallet if it doesn't exist.

```python
env_account = algorand.account.from_environment(
    name="MY_ACCOUNT", fund_with=AlgoAmount(algo=10)
)
```

### KMD account management

When running LocalNet, you have an instance of the [Key Management Daemon](https://github.com/algorand/go-algorand/blob/master/daemon/kmd/README.md), which is useful for:

- Accessing the private key of the default accounts that are pre-seeded with Algo so that other accounts can be funded and it's possible to use LocalNet
- Idempotently creating new accounts against a name that will stay intact while the LocalNet instance is running without you needing to store private keys anywhere (i.e. completely automated)

The KMD SDK is fairly low level so to make use of it there is a fair bit of boilerplate code that's needed. This code has been abstracted away into the `KmdAccountManager` class.

To get an instance of the `KmdAccountManager` class you can access it from [`AlgorandClient`](../algorand-client/) via `algorand.account.kmd` or instantiate it directly (passing in a [`ClientManager`](../client/)):

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
  AlgoAmount.from_algos(2)
)
# This will return the same account as above since the name matches
existing_account = kmd_account_manager.get_or_create_wallet_account(
  "account1"
)
```

Some of this functionality is directly exposed from [`AccountManager`](#accountmanager), which has the added benefit of registering the account as a signer so they can be automatically used to sign transactions when using via [`AlgorandClient`](../algorand-client/):

```python
# Get and register LocalNet dispenser
localnet_dispenser = algorand.account.localnet_dispenser()
# Get and register a dispenser by environment variable, or if not set then LocalNet dispenser via KMD
dispenser = algorand.account.dispenser_from_environment()
# Get an account from KMD idempotently by name. In this case we'll get the default dispenser account
dispenser_via_kmd = algorand.account.from_kmd('unencrypted-default-wallet', lambda a: a.status != 'Offline' and a.amount > 1_000_000_000)
# Get / create and register account from KMD idempotently by name
fresh_account_via_kmd = algorand.account.kmd.get_or_create_wallet_account('account1', AlgoAmount.from_algos(2))
```

## Funding Accounts

All Algorand accounts require a minimum balance to be registered in the ledger. AlgoKit Utils provides helpers to fund accounts from a dispenser, which is particularly useful for automation and deployment scripts.

> [!NOTE]
> For the different funding options across LocalNet, TestNet and MainNet, see [Funding an account](https://dev.algorand.co/concepts/accounts/funding).

### Dispenser accounts

- `localnet_dispenser` - Returns an account with private key loaded that can act as a dispenser for the default LocalNet dispenser account
- `dispenser_from_environment` - Returns an account (with private key loaded) that can act as a dispenser from environment variables, or against default LocalNet if no environment variables present

```python
# The pre-funded default LocalNet dispenser account
localnet_dispenser = algorand.account.localnet_dispenser()

# A dispenser configured via environment variables (falls back to LocalNet)
dispenser = algorand.account.dispenser_from_environment()
```

### Ensure funded

`ensure_funded` checks the balance of an account and transfers Algo from a dispenser if the balance falls below the required spending threshold (accounting for the minimum balance requirement).

```python
algorand.account.ensure_funded(
    account_to_fund=random_account.address,
    dispenser_account=localnet_dispenser.address,
    min_spending_balance=AlgoAmount(algo=10),
)
```

`ensure_funded_from_environment` does the same, but sources the dispenser from the environment (per `dispenser_from_environment`), making the code portable across environments without hardcoding account details.

```python
algorand.account.ensure_funded_from_environment(
    account_to_fund=random_account.address,
    min_spending_balance=AlgoAmount(algo=10),
)
```

### TestNet Dispenser API

`ensure_funded_from_testnet_dispenser_api` tops up an account from the TestNet Dispenser API when its balance is below the threshold. The dispenser client is authenticated via the `ALGOKIT_DISPENSER_ACCESS_TOKEN` environment variable, which is useful for CI/CD pipelines and automated tests.

```python
testnet_dispenser = algorand.client.get_testnet_dispenser()

algorand.account.ensure_funded_from_testnet_dispenser_api(
    account_to_fund=random_account.address,
    dispenser_client=testnet_dispenser,
    min_spending_balance=AlgoAmount(algo=10),
)
```

To fund an account with a fixed amount immediately (without a balance check), use the dispenser client directly.

```python
testnet_dispenser = algorand.client.get_testnet_dispenser()
testnet_dispenser.fund(address=random_account.address, amount=10, asset_id=0)
```

## Keys & Signing

The `AccountManager` keeps track of which signer is associated with a given sender address. This is used by [`AlgorandClient`](../algorand-client/) to automatically sign transactions by that sender. Any of the [account methods](#create-accounts) that return an account will automatically register the signer with the sender.

> [!NOTE]
> For how keys, addresses and mnemonics are derived, and the available signing methods, see [Keys and signing](https://dev.algorand.co/concepts/accounts/keys-signing).

### `TransactionSignerAccountProtocol`

The core internal type that holds information about a signer/sender pair for a transaction is `TransactionSignerAccountProtocol`, which represents an `algosdk.transaction.TransactionSigner` (`signer`) along with a sender address (`address`) as the encoded string address.

The following conform to `TransactionSignerAccountProtocol`:

- `TransactionSignerAccount` - a basic transaction signer account that holds an address and a signer conforming to `TransactionSignerAccountProtocol`
- `SigningAccount` - an abstraction that used to be available under `Account` in previous versions of AlgoKit Utils. Renamed for consistency with equivalent `ts` version. Holds private key and conforms to `TransactionSignerAccountProtocol`
- `LogicSigAccount` - a wrapper class around `algosdk` logicsig abstractions conforming to `TransactionSignerAccountProtocol`
- `MultiSigAccount` - a wrapper class around `algosdk` multisig abstractions conforming to `TransactionSignerAccountProtocol`

#### Underlying account classes

While `TransactionSignerAccount` is the main class used to represent an account that can sign, there are underlying account classes that can underpin the signer within the transaction signer account.

- `TransactionSignerAccount` - A default class conforming to `TransactionSignerAccountProtocol` that holds an address and a signer
- `SigningAccount` - An abstraction around `algosdk.Account` that supports rekeyed accounts
- `LogicSigAccount` - An abstraction around `algosdk.LogicSigAccount` and `algosdk.LogicSig` that supports logic sig signing. Exposes access to the underlying algosdk `algosdk.transaction.LogicSigAccount` object instance via `lsig` property.
- `MultiSigAccount` - An abstraction around `algosdk.MultisigMetadata`, `algosdk.makeMultiSigAccountTransactionSigner`, `algosdk.multisigAddress`, `algosdk.signMultisigTransaction` and `algosdk.appendSignMultisigTransaction` that supports multisig accounts with one or more signers present. Exposes access to the underlying algosdk `algosdk.transaction.Multisig` object instance via `multisig` property.

### Default signer

If you want to have a default signer that is used to sign transactions without a registered signer (rather than throwing an exception) then you can `set_default_signer`:

```python
algorand.account.set_default_signer(account_a.signer)
```

### Registering signers

There are two methods to register a signer: `set_signer_from_account`, which takes any number of [account based objects](#underlying-account-classes) that combine signer and sender (`TransactionSignerAccount` | `SigningAccount` | `LogicSigAccount` | `MultiSigAccount`), or `set_signer` which takes the sender address and the `TransactionSigner`:

```python
# Register multiple signers at once
algorand.account.set_signer_from_account(account_a)
algorand.account.set_signer_from_account(account_b)
algorand.account.set_signer_from_account(account_c)
```

`set_signer_from_account` accepts any of the underlying account classes:

```python
(
    algorand.account
    .set_signer_from_account(TransactionSignerAccount(your_address, your_signer))
    .set_signer_from_account(SigningAccount.new_account())
    .set_signer_from_account(
        LogicSigAccount(algosdk.transaction.LogicSigAccount(program, args))
    )
    .set_signer_from_account(
        MultiSigAccount(
            MultisigMetadata(
                version=1,
                threshold=1,
                addresses=["ADDRESS1...", "ADDRESS2..."],
            ),
            [account1, account2],
        )
    )
    .set_signer("SENDERADDRESS", transaction_signer)
)
```

### Get a signer

[`AlgorandClient`](../algorand-client/) will automatically retrieve a signer when signing a transaction, but if you need to get a `TransactionSigner` externally to do something more custom then you can `get_signer` for a given sender address:

```python
signer = algorand.account.get_signer(account_a.address)
```

If there is no signer registered for that sender address it will either return the default signer ([if registered](#default-signer)) or throw an exception.

### Override the signer

A signer can be overridden per transaction. Create an unsigned transaction and pass the signer explicitly when adding it to a group:

```python
account_b_signer = algorand.account.get_signer(account_b.address)

# Create an unsigned payment transaction
payment_txn = algorand.create_transaction.payment(
    PaymentParams(
        sender=account_a.address,
        receiver=account_b.address,
        amount=AlgoAmount(algo=1),
        note=b"Payment from A to B",
    )
)

# The transaction signer can be overridden in the `add_transaction` call
algorand.new_group().add_transaction(
    transaction=payment_txn, signer=account_b_signer
).send()
```

## Rekeying Accounts

One of the unique features of Algorand is the ability to change the private key that can authorise transactions for an account. This is called [rekeying](https://dev.algorand.co/concepts/accounts/rekeying).

> [!WARNING]
> Rekeying should be done with caution as a rekey transaction can result in permanent loss of control of an account.

You can issue a transaction to rekey an account by using the `rekey_account` function:

- `account: string | TransactionSignerAccount` - The account address or signing account of the account that will be rekeyed
- `rekey_to: string | TransactionSignerAccount` - The account address or signing account of the account that will be used to authorise transactions for the rekeyed account going forward. If a signing account is provided that will now be tracked as the signer for `account` in the `AccountManager` instance.
- An `options` object, which has:
  - [Common transaction parameters](../algorand-client/#transaction-parameters)
  - [Execution parameters](../algorand-client/#sending-a-single-transaction)

You can also pass in `rekey_to` as a [common transaction parameter](../algorand-client/#transaction-parameters) to any transaction.

In the following example, `account_a` is rekeyed to `account_b`. After rekeying, a transaction from `account_a` must be authorised by `account_b`'s private key.

```python
# Rekey account_a so that account_b's key now authorises its transactions
algorand.account.rekey_account(account=account_a.address, rekey_to=account_b)

# Signing with account_b succeeds; signing with account_a would now fail
unsigned_payment_txn = algorand.create_transaction.payment(
    PaymentParams(
        sender=account_a.address,
        receiver=account_b.address,
        amount=AlgoAmount(algo=1),
    )
)

result = (
    algorand.new_group()
    .add_transaction(transaction=unsigned_payment_txn, signer=account_b.signer)
    .send()
)
```

> [!NOTE]
> If a signing account is passed into `algorand.account.rekey_account` then you don't need to call `rekeyed` to register the new signer — it is tracked automatically.

## Multisignature Accounts

A multisignature account is an ordered set of addresses with a threshold and version. The threshold determines how many signatures are required to authorise a transaction (such as 2-of-3 or 3-of-5).

> [!NOTE]
> For how multisig accounts work at the protocol level, weighted signers and ARC-55 coordination, see [Multisignature accounts](https://dev.algorand.co/concepts/accounts/multisig).

Use `multisig` to register and return a multisig account with one or more signing keys loaded. The example below creates a 2-of-3 multisig account that requires only 2 signatures from the 3 possible signers to authorise transactions.

```python
from algokit_utils import AlgoAmount, MultisigMetadata, PaymentParams

multisig_account = algorand.account.multisig(
    metadata=MultisigMetadata(
        version=1,
        threshold=2,
        addresses=[
            account_a.address,
            account_b.address,
            account_c.address,
        ],
    ),
    signing_accounts=[account_a, account_b, account_c],
)

# A multisig account must be funded to initialise its state on the ledger
algorand.account.ensure_funded(
    multisig_account.address, dispenser, AlgoAmount(algo=10)
)

# Send a payment from the multisig account. The required number of signatures
# is collected automatically from the signing accounts provided above.
algorand.send.payment(
    PaymentParams(
        sender=multisig_account.address,
        receiver=account_a.address,
        amount=AlgoAmount(algo=1),
    ),
)
```
