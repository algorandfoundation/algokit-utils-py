# algokit_utils.transactions.composer_resources

## Classes

| [`GroupResourceType`](#algokit_utils.transactions.composer_resources.GroupResourceType)             | Create a collection of name/value pairs.   |
|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| [`GroupResourceToPopulate`](#algokit_utils.transactions.composer_resources.GroupResourceToPopulate) |                                            |

## Functions

| [`populate_transaction_resources`](#algokit_utils.transactions.composer_resources.populate_transaction_resources)(...)   | Populate transaction-level resources for app call transactions   |
|--------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`populate_group_resources`](#algokit_utils.transactions.composer_resources.populate_group_resources)(→ None)            | Populate group-level resources for app call transactions         |

## Module Contents

### algokit_utils.transactions.composer_resources.populate_transaction_resources(transaction: algokit_transact.models.transaction.Transaction, resources_accessed: algokit_algod_client.models.SimulateUnnamedResourcesAccessed, group_index: int) → algokit_transact.models.transaction.Transaction

Populate transaction-level resources for app call transactions

### *class* algokit_utils.transactions.composer_resources.GroupResourceType(\*args, \*\*kwds)

Bases: `enum.Enum`

Create a collection of name/value pairs.

Example enumeration:

```python
class Color(Enum):
    RED = 1
    BLUE = 2
    GREEN = 3
```

Access them by:

- attribute access:
  ```python
  Color.RED
  <Color.RED: 1>
  ```
- value lookup:
  ```python
  Color(1)
  <Color.RED: 1>
  ```
- name lookup:
  ```python
  Color['RED']
  <Color.RED: 1>
  ```

Enumerations can be iterated over, and know how many members they have:

```python
len(Color)
3
```

```python
list(Color)
[<Color.RED: 1>, <Color.BLUE: 2>, <Color.GREEN: 3>]
```

Methods can be added to enumerations, and members can have their own
attributes – see the documentation for details.

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
