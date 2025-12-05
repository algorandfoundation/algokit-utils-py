# algokit_utils.models.account

## Attributes

| [`DISPENSER_ACCOUNT_NAME`](#algokit_utils.models.account.DISPENSER_ACCOUNT_NAME)   |    |
|------------------------------------------------------------------------------------|----|

## Classes

| [`TransactionSignerAccount`](#algokit_utils.models.account.TransactionSignerAccount)   | A basic transaction signer account.                                                     |
|----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| [`SigningAccount`](#algokit_utils.models.account.SigningAccount)                       | Account with private key. Implements SignerAccountProtocol.                             |
| [`MultisigMetadata`](#algokit_utils.models.account.MultisigMetadata)                   | Metadata for a multisig account.                                                        |
| [`MultiSigAccount`](#algokit_utils.models.account.MultiSigAccount)                     | Account wrapper for multisig signing. Supports secretless signing.                      |
| [`LogicSigAccount`](#algokit_utils.models.account.LogicSigAccount)                     | Account wrapper for LogicSig signing. Supports delegation including secretless signing. |

## Module Contents

### algokit_utils.models.account.DISPENSER_ACCOUNT_NAME *= 'DISPENSER'*

### *class* algokit_utils.models.account.TransactionSignerAccount

A basic transaction signer account.

#### address *: str*

#### signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

### *class* algokit_utils.models.account.SigningAccount

Account with private key. Implements SignerAccountProtocol.

#### private_key *: str*

Base64 encoded private key

#### address *: str* *= ''*

Address for this account

#### *property* public_key *: bytes*

The public key for this account.

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

Transaction signer callable.

#### *property* bytes_signer *: [algokit_utils.protocols.signer.BytesSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.BytesSigner)*

Raw bytes signer.

#### *property* lsig_signer *: [algokit_utils.protocols.signer.LsigSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.LsigSigner)*

LogicSig program signer.

#### *property* program_data_signer *: [algokit_utils.protocols.signer.ProgramDataSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.ProgramDataSigner)*

Program data signer (ProgData prefix).

#### *property* mx_bytes_signer *: [algokit_utils.protocols.signer.MxBytesSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.MxBytesSigner)*

MX-prefixed bytes signer.

### *class* algokit_utils.models.account.MultisigMetadata

Metadata for a multisig account.

#### version *: int*

#### threshold *: int*

#### addresses *: list[str]*

### *class* algokit_utils.models.account.MultiSigAccount(multisig_params: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata), signing_accounts: collections.abc.Sequence[[algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)])

Account wrapper for multisig signing. Supports secretless signing.

#### *property* params *: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata)*

The multisig account parameters.

#### *property* signing_accounts *: collections.abc.Sequence[[algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)]*

The list of signing accounts.

#### *property* address *: str*

The multisig account address.

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

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

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../../protocols/signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

Transaction signer callable.

#### delegate(account: [algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)) → [LogicSigAccount](#algokit_utils.models.account.LogicSigAccount)

Delegate this LogicSig to a single account. Returns self for chaining.

#### delegate_multisig(multisig_params: [MultisigMetadata](#algokit_utils.models.account.MultisigMetadata), signing_accounts: collections.abc.Sequence[[algokit_utils.protocols.account.SignerAccountProtocol](../../protocols/account/index.md#algokit_utils.protocols.account.SignerAccountProtocol)]) → [LogicSigAccount](#algokit_utils.models.account.LogicSigAccount)

Delegate this LogicSig to a multisig account. Returns self for chaining.

#### *property* lsig *: AlgosdkLogicSigAccount*

Get algosdk LogicSigAccount (creates new instance each time).

#### *property* algokit_lsig *: AlgosdkLogicSigAccount*

Deprecated: Use lsig property instead.
