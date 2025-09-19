# algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults

#### *class* algokit_utils.transactions.transaction_composer.SendAtomicTransactionComposerResults

Results from sending an AtomicTransactionComposer transaction group.

#### group_id *: str*

The group ID if this was a transaction group

#### confirmations *: list[algosdk.v2client.algod.AlgodResponseType]*

The confirmation info for each transaction

#### tx_ids *: list[str]*

The transaction IDs that were sent

#### transactions *: list[[algokit_utils.models.transaction.TransactionWrapper](../../models/transaction/TransactionWrapper.md#algokit_utils.models.transaction.TransactionWrapper)]*

The transactions that were sent

#### returns *: list[[algokit_utils.applications.abi.ABIReturn](../../applications/abi/ABIReturn.md#algokit_utils.applications.abi.ABIReturn)]*

The ABI return values from any ABI method calls

#### simulate_response *: dict[str, Any] | None* *= None*

The simulation response if simulation was performed, defaults to None
