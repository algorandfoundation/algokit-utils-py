# algokit_utils.models.account

## Attributes

| [`DISPENSER_ACCOUNT_NAME`](#algokit_utils.models.account.DISPENSER_ACCOUNT_NAME)   |    |
|------------------------------------------------------------------------------------|----|

## Classes

| [`MultisigMetadata`](#algokit_utils.models.account.MultisigMetadata)   | Metadata for a multisig account.                                                        |
|------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| [`MultisigAccount`](#algokit_utils.models.account.MultisigAccount)     | Account wrapper for multisig signing. Supports secretless signing.                      |
| [`LogicSigAccount`](#algokit_utils.models.account.LogicSigAccount)     | Account wrapper for LogicSig signing. Supports delegation including secretless signing. |

## Module Contents

### algokit_utils.models.account.DISPENSER_ACCOUNT_NAME *= 'DISPENSER'*

### *class* algokit_utils.models.account.MultisigMetadata

Metadata for a multisig account.

#### version *: int*

#### threshold *: int*

#### addresses *: list[str]*

### *class* algokit_utils.models.account.MultisigAccount(multisig_params: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata), sub_signers: collections.abc.Sequence[algokit_transact.signer.AddressWithSigners])

Account wrapper for multisig signing. Supports secretless signing.

#### *property* params *: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata)*

The multisig account parameters.

#### *property* sub_signers *: collections.abc.Sequence[algokit_transact.signer.AddressWithSigners]*

The list of signing accounts.

#### *property* address *: str*

The multisig account address.

#### *property* addr *: str*

Alias for address property (matching TypeScript’s get addr()).

#### *property* signer *: algokit_transact.signer.TransactionSigner*

Transaction signer callable.

### *class* algokit_utils.models.account.LogicSigAccount(program: bytes, args: list[bytes] | None = None)

Account wrapper for LogicSig signing. Supports delegation including secretless signing.

#### *property* program *: bytes*

The LogicSig program bytes.

#### *property* args *: list[bytes] | None*

The arguments to pass to the LogicSig program.

#### *property* is_delegated *: bool*

Whether this LogicSig is delegated to an account.

#### *property* address *: str*

The LogicSig account address (delegated address or escrow address).

#### *property* addr *: str*

Alias for address property (matching TypeScript’s get addr()).

#### *property* signer *: algokit_transact.signer.TransactionSigner*

Transaction signer callable.

#### bytes_to_sign_for_delegation(msig: [MultisigAccount](#algokit_utils.models.account.MultisigAccount) | None = None) → bytes

Returns bytes to sign for delegation.

Args:
: msig: Optional multisig account for multisig delegation.

Returns:
: The bytes that need to be signed for delegation.

#### program_data_to_sign(data: bytes) → bytes

Returns bytes to sign for program data.

Args:
: data: The data to sign.

Returns:
: The bytes that need to be signed (ProgData + program_address + data).

#### sign_program_data(data: bytes, signer: algokit_transact.signer.ProgramDataSigner) → bytes

Signs program data with given signer.

Args:
: data: The data to sign.
  signer: The program data signer to use.

Returns:
: The signature bytes.

#### delegate(signer: algokit_transact.signer.DelegatedLsigSigner, delegating_address: str | None = None) → [LogicSigAccount](#algokit_utils.models.account.LogicSigAccount)

Delegate this LogicSig to a single account. Returns self for chaining.

Args:
: signer: The DelegatedLsigSigner callback to sign the program.
  delegating_address: Optional address of the delegating account.
  <br/>
  > If not provided, the address must be set separately or
  > the LogicSig will use the escrow address.

Returns:
: Self for method chaining.

#### delegate_multisig(multisig_params: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata), signing_accounts: collections.abc.Sequence[algokit_transact.signer.AddressWithSigners]) → [LogicSigAccount](#algokit_utils.models.account.LogicSigAccount)

Delegate this LogicSig to a multisig account. Returns self for chaining.
