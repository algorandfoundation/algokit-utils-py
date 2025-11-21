# algokit_utils.models.account

## Attributes

| [`DISPENSER_ACCOUNT_NAME`](#algokit_utils.models.account.DISPENSER_ACCOUNT_NAME)   |    |
|------------------------------------------------------------------------------------|----|

## Classes

| [`TransactionSignerAccount`](#algokit_utils.models.account.TransactionSignerAccount)   | A basic transaction signer account.                             |
|----------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`SigningAccount`](#algokit_utils.models.account.SigningAccount)                       | Holds the private key and address for an account.               |
| [`MultisigMetadata`](#algokit_utils.models.account.MultisigMetadata)                   | Metadata for a multisig account.                                |
| [`MultiSigAccount`](#algokit_utils.models.account.MultiSigAccount)                     | Account wrapper that supports partial or full multisig signing. |
| [`LogicSigAccount`](#algokit_utils.models.account.LogicSigAccount)                     | Account wrapper that supports logic sig signing.                |

## Module Contents

### algokit_utils.models.account.DISPENSER_ACCOUNT_NAME *= 'DISPENSER'*

### *class* algokit_utils.models.account.TransactionSignerAccount

A basic transaction signer account.

#### address *: str*

#### signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

### *class* algokit_utils.models.account.SigningAccount

Holds the private key and address for an account.

Provides access to the account’s private key, address, public key and transaction signer.

#### private_key *: str*

Base64 encoded private key

#### address *: str* *= ''*

Address for this account

#### *property* public_key *: bytes*

The public key for this account.

* **Returns:**
  The public key as bytes

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

Get the AlgoKit-native transaction signer callable.

### *class* algokit_utils.models.account.MultisigMetadata

Metadata for a multisig account.

Contains the version, threshold and addresses for a multisig account.

#### version *: int*

#### threshold *: int*

#### addresses *: list[str]*

### *class* algokit_utils.models.account.MultiSigAccount(multisig_params: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata), signing_accounts: list[[SigningAccount](#algokit_utils.models.account.SigningAccount)])

Account wrapper that supports partial or full multisig signing.

Provides functionality to manage and sign transactions for a multisig account.

* **Parameters:**
  * **multisig_params** – The parameters for the multisig account
  * **signing_accounts** – The list of accounts that can sign

#### *property* multisig *: algokit_algosdk.transaction.Multisig*

Get the underlying algosdk.transaction.Multisig object instance.

* **Returns:**
  The algosdk.transaction.Multisig object instance

#### *property* params *: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata)*

Get the parameters for the multisig account.

* **Returns:**
  The multisig account parameters

#### *property* signing_accounts *: list[[SigningAccount](#algokit_utils.models.account.SigningAccount)]*

Get the list of accounts that are present to sign.

* **Returns:**
  The list of signing accounts

#### *property* address *: str*

Get the address of the multisig account.

* **Returns:**
  The multisig account address

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

Get the AlgoKit-native signer callable for this multisig account.

#### sign(transaction: algokit_transact.models.transaction.Transaction) → algokit_algosdk.transaction.MultisigTransaction

Sign the given transaction with all present signers.

* **Parameters:**
  **transaction** – Either a transaction object or a raw, partially signed transaction
* **Returns:**
  The transaction signed by the present signers

### *class* algokit_utils.models.account.LogicSigAccount(program: bytes, args: list[bytes] | None)

Account wrapper that supports logic sig signing.

Provides functionality to manage and sign transactions for a logic sig account.

#### *property* lsig *: AlgosdkLogicSigAccount*

Get the underlying algosdk.transaction.LogicSigAccount object instance.

* **Returns:**
  The algosdk.transaction.LogicSigAccount object instance

#### *property* address *: str*

Get the address of the logic sig account.

If the LogicSig is delegated to another account, this will return the address of that account.

If the LogicSig is not delegated to another account, this will return an escrow address that is the hash of
the LogicSig’s program code.

* **Returns:**
  The logic sig account address

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

Get the AlgoKit-native signer callable for this logic sig account.

#### *property* algokit_lsig *: algokit_algosdk.logicsig.LogicSigAccount*

Expose the AlgoKit-native representation.
