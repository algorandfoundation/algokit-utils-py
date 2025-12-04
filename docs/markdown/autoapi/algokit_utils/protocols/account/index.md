# algokit_utils.protocols.account

## Classes

| [`TransactionSignerAccountProtocol`](#algokit_utils.protocols.account.TransactionSignerAccountProtocol)   | An account that has a transaction signer.                         |
|-----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| [`SignerAccountProtocol`](#algokit_utils.protocols.account.SignerAccountProtocol)                         | Protocol for an account that provides multiple signer interfaces. |

## Module Contents

### *class* algokit_utils.protocols.account.TransactionSignerAccountProtocol

Bases: `Protocol`

An account that has a transaction signer.
Implemented by SigningAccount, LogicSigAccount, MultiSigAccount and TransactionSignerAccount abstractions.

#### *property* address *: str*

The address of the account.

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

The AlgoKit-native signer callable.

### *class* algokit_utils.protocols.account.SignerAccountProtocol

Bases: `Protocol`

Protocol for an account that provides multiple signer interfaces.

This protocol extends the basic TransactionSignerAccountProtocol with
additional signing capabilities for LogicSig delegation and raw bytes signing.
It enables secretless signing through KMS, hardware wallets, or other
external signing mechanisms.

Implementations of this protocol can be used:
- As sub-signers in MultisigAccount
- To delegate LogicSig accounts
- For any operation requiring account-based signing

See Also:
: - make_signer_account: Factory function to create SignerAccountProtocol from a BytesSigner
  - SigningAccount: Standard implementation using private keys

#### *property* address *: str*

The address of the account.

#### *property* public_key *: bytes*

The public key for this account (32 bytes).

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

The AlgoKit-native transaction signer callable.

#### *property* lsig_signer *: [algokit_utils.protocols.signer.LsigSigner](../signer/index.md#algokit_utils.protocols.signer.LsigSigner)*

Signer for LogicSig programs.

Signs programs with appropriate domain prefix based on whether
msig_address is provided:
- None: “Program” + program (single-sig delegation)
- bytes: “MsigProgram” + msig_address + program (multisig delegation)

#### *property* program_data_signer *: [algokit_utils.protocols.signer.ProgramDataSigner](../signer/index.md#algokit_utils.protocols.signer.ProgramDataSigner)*

Signer for program data (LogicSig data).

Signs data prefixed with “ProgData” domain separator.
Used during transaction signing with delegated LogicSigs.

#### *property* bytes_signer *: [algokit_utils.protocols.signer.BytesSigner](../signer/index.md#algokit_utils.protocols.signer.BytesSigner)*

Raw bytes signer.

Signs arbitrary bytes without domain prefix.
This is the lowest-level signer interface.

#### *property* mx_bytes_signer *: [algokit_utils.protocols.signer.MxBytesSigner](../signer/index.md#algokit_utils.protocols.signer.MxBytesSigner)*

Signer for arbitrary bytes with MX domain prefix.

Signs bytes prefixed with “MX” domain separator.
Used for signing arbitrary messages.
