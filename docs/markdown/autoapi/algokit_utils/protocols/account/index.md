# algokit_utils.protocols.account

## Classes

| [`TransactionSignerAccountProtocol`](#algokit_utils.protocols.account.TransactionSignerAccountProtocol)   | An account that has a transaction signer.                            |
|-----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`SignerAccountProtocol`](#algokit_utils.protocols.account.SignerAccountProtocol)                         | Account providing multiple signer interfaces for secretless signing. |

## Module Contents

### *class* algokit_utils.protocols.account.TransactionSignerAccountProtocol

Bases: `Protocol`

An account that has a transaction signer.
Implemented by SigningAccount, LogicSigAccount, MultiSigAccount and TransactionSignerAccount abstractions.

#### *property* address *: str*

The address of the account.

#### *property* signer *: algokit_transact.signer.TransactionSigner*

The AlgoKit-native signer callable.

### *class* algokit_utils.protocols.account.SignerAccountProtocol

Bases: `Protocol`

Account providing multiple signer interfaces for secretless signing.

#### *property* address *: str*

#### *property* public_key *: bytes*

#### *property* signer *: algokit_transact.signer.TransactionSigner*

#### *property* lsig_signer *: algokit_transact.signer.LsigSigner*

#### *property* program_data_signer *: algokit_transact.signer.ProgramDataSigner*

#### *property* bytes_signer *: algokit_transact.signer.BytesSigner*

#### *property* mx_bytes_signer *: algokit_transact.signer.MxBytesSigner*
