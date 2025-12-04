# algokit_utils.protocols.signer

## Classes

| [`TransactionSigner`](#algokit_utils.protocols.signer.TransactionSigner)   | Signature for AlgoKit-native transaction signers.             |
|----------------------------------------------------------------------------|---------------------------------------------------------------|
| [`BytesSigner`](#algokit_utils.protocols.signer.BytesSigner)               | Protocol for a raw bytes signer.                              |
| [`ProgramDataSigner`](#algokit_utils.protocols.signer.ProgramDataSigner)   | Protocol for signing program data (LogicSig data).            |
| [`LsigSigner`](#algokit_utils.protocols.signer.LsigSigner)                 | Protocol for signing LogicSig programs for delegation.        |
| [`MxBytesSigner`](#algokit_utils.protocols.signer.MxBytesSigner)           | Protocol for signing arbitrary bytes with "MX" domain prefix. |

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

Protocol for signing LogicSig programs for delegation.

Signs programs with appropriate domain prefix:
- Single-sig delegation: “Program” + program
- Multisig delegation: “MsigProgram” + msig_address + program

The msig_address parameter determines which mode is used.

Example:
: def my_lsig_signer(program: bytes, msig_address: bytes | None = None) -> bytes:
  : if msig_address:
    : # Sign: b”MsigProgram” + msig_address + program
      return signature_bytes
    <br/>
    else:
    : # Sign: b”Program” + program
      return signature_bytes

### *class* algokit_utils.protocols.signer.MxBytesSigner

Bases: `Protocol`

Protocol for signing arbitrary bytes with “MX” domain prefix.

Signs bytes prefixed with “MX” domain separator, following Algorand’s
domain-separated signing convention for arbitrary data.
This is used for signing arbitrary messages that aren’t transactions,
programs, or program data.

Example:
: def my_mx_bytes_signer(data: bytes) -> bytes:
  : # Sign: b”MX” + data
    return signature_bytes
