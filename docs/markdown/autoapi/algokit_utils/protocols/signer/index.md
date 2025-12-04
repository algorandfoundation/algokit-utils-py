# algokit_utils.protocols.signer

## Classes

| [`TransactionSigner`](#algokit_utils.protocols.signer.TransactionSigner)   | Signature for AlgoKit-native transaction signers.   |
|----------------------------------------------------------------------------|-----------------------------------------------------|
| [`BytesSigner`](#algokit_utils.protocols.signer.BytesSigner)               | Protocol for a raw bytes signer.                    |
| [`ProgramDataSigner`](#algokit_utils.protocols.signer.ProgramDataSigner)   | Protocol for signing program data (LogicSig data).  |
| [`LsigSigner`](#algokit_utils.protocols.signer.LsigSigner)                 | Protocol for signing LogicSig programs.             |

## Module Contents

### *class* algokit_utils.protocols.signer.TransactionSigner

Bases: `Protocol`

Signature for AlgoKit-native transaction signers.

### *class* algokit_utils.protocols.signer.BytesSigner

Bases: `Protocol`

Protocol for a raw bytes signer.

Signs arbitrary bytes (typically an ed25519 signature over the input).
This is the lowest-level signer interface, used to build higher-level signers.

Example:
: def my_bytes_signer(data: bytes) -> bytes:
  : # Sign using KMS, hardware wallet, etc.
    return signature_bytes

### *class* algokit_utils.protocols.signer.ProgramDataSigner

Bases: `Protocol`

Protocol for signing program data (LogicSig data).

Signs data prefixed with the “ProgData” domain separator.
Used for delegated LogicSig signatures where the signature
covers the program hash concatenated with the transaction data.

Example:
: def my_program_data_signer(data: bytes) -> bytes:
  : # Sign: b”ProgData” + data
    return signature_bytes

### *class* algokit_utils.protocols.signer.LsigSigner

Bases: `Protocol`

Protocol for signing LogicSig programs.

Signs the program itself prefixed with the “Program” domain separator.
Used when delegating a LogicSig to an account (single-sig delegation).

Example:
: def my_lsig_signer(program: bytes) -> bytes:
  : # Sign: b”Program” + program
    return signature_bytes
