# algokit_utils.protocols.signer

## Classes

| [`TransactionSigner`](#algokit_utils.protocols.signer.TransactionSigner)   | Signature for AlgoKit-native transaction signers.                             |
|----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`BytesSigner`](#algokit_utils.protocols.signer.BytesSigner)               | Raw bytes signer (ed25519 signature over input).                              |
| [`ProgramDataSigner`](#algokit_utils.protocols.signer.ProgramDataSigner)   | Signs data with "ProgData" domain prefix for delegated LogicSig transactions. |
| [`LsigSigner`](#algokit_utils.protocols.signer.LsigSigner)                 | Signs LogicSig programs for delegation.                                       |
| [`MxBytesSigner`](#algokit_utils.protocols.signer.MxBytesSigner)           | Signs arbitrary bytes with "MX" domain prefix.                                |

## Module Contents

### *class* algokit_utils.protocols.signer.TransactionSigner

Bases: `Protocol`

Signature for AlgoKit-native transaction signers.

### *class* algokit_utils.protocols.signer.BytesSigner

Bases: `Protocol`

Raw bytes signer (ed25519 signature over input).

### *class* algokit_utils.protocols.signer.ProgramDataSigner

Bases: `Protocol`

Signs data with “ProgData” domain prefix for delegated LogicSig transactions.

### *class* algokit_utils.protocols.signer.LsigSigner

Bases: `Protocol`

Signs LogicSig programs for delegation.

Without msig_address: signs “Program” + program
With msig_address: signs “MsigProgram” + msig_address + program

### *class* algokit_utils.protocols.signer.MxBytesSigner

Bases: `Protocol`

Signs arbitrary bytes with “MX” domain prefix.
