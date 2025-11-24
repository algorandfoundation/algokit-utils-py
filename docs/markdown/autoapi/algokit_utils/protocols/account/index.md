# algokit_utils.protocols.account

## Classes

| [`TransactionSignerAccountProtocol`](#algokit_utils.protocols.account.TransactionSignerAccountProtocol)   | An account that has a transaction signer.   |
|-----------------------------------------------------------------------------------------------------------|---------------------------------------------|

## Module Contents

### *class* algokit_utils.protocols.account.TransactionSignerAccountProtocol

Bases: `Protocol`

An account that has a transaction signer.
Implemented by SigningAccount, LogicSigAccount, MultiSigAccount and TransactionSignerAccount abstractions.

#### *property* address *: str*

The address of the account.

#### *property* signer *: [algokit_utils.protocols.signer.TransactionSigner](../signer/index.md#algokit_utils.protocols.signer.TransactionSigner)*

The AlgoKit-native signer callable.
