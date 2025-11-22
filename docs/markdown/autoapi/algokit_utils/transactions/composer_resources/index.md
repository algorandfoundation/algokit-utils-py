# algokit_utils.transactions.composer_resources

## Classes

| [`GroupResourceType`](#algokit_utils.transactions.composer_resources.GroupResourceType)             | Generic enumeration.   |
|-----------------------------------------------------------------------------------------------------|------------------------|
| [`GroupResourceToPopulate`](#algokit_utils.transactions.composer_resources.GroupResourceToPopulate) |                        |

## Functions

| [`populate_transaction_resources`](#algokit_utils.transactions.composer_resources.populate_transaction_resources)(...)   | Populate transaction-level resources for app call transactions   |
|--------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`populate_group_resources`](#algokit_utils.transactions.composer_resources.populate_group_resources)(→ None)            | Populate group-level resources for app call transactions         |

## Module Contents

### algokit_utils.transactions.composer_resources.populate_transaction_resources(transaction: algokit_transact.models.transaction.Transaction, resources_accessed: algokit_algod_client.models.SimulateUnnamedResourcesAccessed, group_index: int) → algokit_transact.models.transaction.Transaction

Populate transaction-level resources for app call transactions

### *class* algokit_utils.transactions.composer_resources.GroupResourceType

Bases: `enum.Enum`

Generic enumeration.

Derive from this class to define new enumerations.

#### Account *= 'Account'*

#### App *= 'App'*

#### Asset *= 'Asset'*

#### Box *= 'Box'*

#### ExtraBoxRef *= 'ExtraBoxRef'*

#### AssetHolding *= 'AssetHolding'*

#### AppLocal *= 'AppLocal'*

### *class* algokit_utils.transactions.composer_resources.GroupResourceToPopulate

#### type *: [GroupResourceType](#algokit_utils.transactions.composer_resources.GroupResourceType)*

#### data *: Any*

### algokit_utils.transactions.composer_resources.populate_group_resources(transactions: list[algokit_transact.models.transaction.Transaction], group_resources: algokit_algod_client.models.SimulateUnnamedResourcesAccessed) → None

Populate group-level resources for app call transactions
