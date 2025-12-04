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
Implements SignerAccountProtocol for use with MultisigAccount and LogicSig delegation.

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

#### *property* bytes_signer *: [algokit_utils.protocols.signer.BytesSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.BytesSigner)*

Get a raw bytes signer for this account.

Signs arbitrary bytes with the account’s private key.

#### *property* lsig_signer *: [algokit_utils.protocols.signer.LsigSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.LsigSigner)*

Get a LogicSig program signer for this account.

Signs programs with “Program” domain prefix for LogicSig delegation.

#### *property* program_data_signer *: [algokit_utils.protocols.signer.ProgramDataSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.ProgramDataSigner)*

Get a program data signer for this account.

Signs data with “ProgData” domain prefix for delegated LogicSig transactions.

### *class* algokit_utils.models.account.MultisigMetadata

Metadata for a multisig account.

Contains the version, threshold and addresses for a multisig account.

#### version *: int*

#### threshold *: int*

#### addresses *: list[str]*

### *class* algokit_utils.models.account.MultiSigAccount(multisig_params: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata), signing_accounts: collections.abc.Sequence[[algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)])

Account wrapper that supports partial or full multisig signing.

Provides functionality to manage and sign transactions for a multisig account.
Supports secretless signing through SignerAccountProtocol implementations.

* **Parameters:**
  * **multisig_params** – The parameters for the multisig account
  * **signing_accounts** – List of accounts that can sign. Can be SigningAccount
    or any SignerAccountProtocol implementation (for secretless signing)

#### *property* params *: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata)*

Get the parameters for the multisig account.

* **Returns:**
  The multisig account parameters

#### *property* signing_accounts *: collections.abc.Sequence[[algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)]*

Get the list of accounts that are present to sign.

* **Returns:**
  The list of signing accounts

#### *property* address *: str*

Get the address of the multisig account.

* **Returns:**
  The multisig account address

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

Get the AlgoKit-native signer callable for this multisig account.

### *class* algokit_utils.models.account.LogicSigAccount(program: bytes, args: list[bytes] | None = None)

Account wrapper that supports logic sig signing.

Provides functionality to manage and sign transactions for a logic sig account.
Supports delegation to single accounts or multisig accounts, including secretless signing.

Examples:
: # Escrow LogicSig (no delegation)
  lsig = LogicSigAccount(program=compiled_teal, args=None)
  <br/>
  # Delegated to single account
  lsig = LogicSigAccount(program=compiled_teal, args=None)
  lsig.delegate(signing_account)
  <br/>
  # Delegated to multisig
  lsig = LogicSigAccount(program=compiled_teal, args=None)
  lsig.delegate_multisig(multisig_params, [signer1, signer2])

#### *property* program *: bytes*

The LogicSig program bytes.

#### *property* args *: list[bytes] | None*

The arguments to pass to the LogicSig program.

#### *property* is_delegated *: bool*

Whether this LogicSig is delegated to an account.

#### *property* address *: str*

Get the address of the logic sig account.

If the LogicSig is delegated to another account, this will return the address of that account.
If the LogicSig is not delegated to another account, this will return an escrow address that is
the hash of the LogicSig’s program code.

* **Returns:**
  The logic sig account address

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

Get the AlgoKit-native signer callable for this logic sig account.

#### delegate(account: [algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)) → [LogicSigAccount](#algokit_utils.models.account.LogicSigAccount)

Delegate this LogicSig to a single account.

The account’s lsig_signer will be used to sign the program,
allowing the LogicSig to be used on behalf of the account.

Args:
: account: An account implementing SignerAccountProtocol.
  : Can be a SigningAccount or a secretless signer account.

Returns:
: Self for method chaining.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  lsig = LogicSigAccount(program=compiled_teal)
  lsig.delegate(signing_account)
  <br/>
  # Now the LogicSig’s address is the signing_account’s address
  assert lsig.address == signing_account.address
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### delegate_multisig(multisig_params: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata), signing_accounts: collections.abc.Sequence[[algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)]) → [LogicSigAccount](#algokit_utils.models.account.LogicSigAccount)

Delegate this LogicSig to a multisig account.

The signing accounts’ lsig_signers will be used to sign the program.
At least threshold signatures are needed for the LogicSig to be valid.

Args:
: multisig_params: The multisig parameters (version, threshold, addresses)
  signing_accounts: List of accounts to sign with. These should be
  <br/>
  > participants in the multisig. Can include SigningAccount
  > or secretless signer accounts.

Returns:
: Self for method chaining.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  lsig = LogicSigAccount(program=compiled_teal)
  lsig.delegate_multisig(
  <br/>
  > MultisigMetadata(version=1, threshold=2, addresses=[addr1, addr2, addr3]),
  > [signer1, signer2]  # 2 of 3 signers
  <br/>
  )
  <br/>
  # Now the LogicSig’s address is the multisig address
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### *property* lsig *: AlgosdkLogicSigAccount*

Get the underlying algosdk.transaction.LogicSigAccount object instance.

Note: This creates a new instance each time for compatibility.
Prefer using the signer property for signing transactions.

* **Returns:**
  The algosdk.transaction.LogicSigAccount object instance

#### *property* algokit_lsig *: AlgosdkLogicSigAccount*

Expose the AlgoKit-native representation.

Deprecated: Use lsig property instead.
