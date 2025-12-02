# algokit_utils.transactions.fee_coverage

## Classes

| [`FeeDeltaType`](#algokit_utils.transactions.fee_coverage.FeeDeltaType)   | Create a collection of name/value pairs.                                                   |
|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| [`FeeDelta`](#algokit_utils.transactions.fee_coverage.FeeDelta)           | Represents a difference between required and provided fee amounts.                         |
| [`FeePriority`](#algokit_utils.transactions.fee_coverage.FeePriority)     | Priority wrapper used when deciding which transactions need additional fees applied first. |

## Module Contents

### *class* algokit_utils.transactions.fee_coverage.FeeDeltaType(\*args, \*\*kwds)

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

#### DEFICIT

#### SURPLUS

### *class* algokit_utils.transactions.fee_coverage.FeeDelta

Represents a difference between required and provided fee amounts.

#### type *: [FeeDeltaType](#algokit_utils.transactions.fee_coverage.FeeDeltaType)*

#### data *: int*

#### *static* from_int(value: int) → [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta) | None

#### *static* add(lhs: [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta) | None, rhs: [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta) | None) → [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta) | None

#### *static* to_int(delta: [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta)) → int

#### *static* amount(delta: [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta)) → int

#### *static* is_deficit(delta: [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta)) → bool

#### *static* is_surplus(delta: [FeeDelta](#algokit_utils.transactions.fee_coverage.FeeDelta)) → bool

### *class* algokit_utils.transactions.fee_coverage.FeePriority

Priority wrapper used when deciding which transactions need additional fees applied first.

#### priority_level *: int*

#### deficit_amount *: int*

#### Covered *: ClassVar[[FeePriority](#algokit_utils.transactions.fee_coverage.FeePriority)]*

#### ModifiableDeficit *: ClassVar[collections.abc.Callable[[int], [FeePriority](#algokit_utils.transactions.fee_coverage.FeePriority)]]*

#### ImmutableDeficit *: ClassVar[collections.abc.Callable[[int], [FeePriority](#algokit_utils.transactions.fee_coverage.FeePriority)]]*

#### *static* covered() → [FeePriority](#algokit_utils.transactions.fee_coverage.FeePriority)

#### *static* modifiable_deficit(amount: int) → [FeePriority](#algokit_utils.transactions.fee_coverage.FeePriority)

#### *static* immutable_deficit(amount: int) → [FeePriority](#algokit_utils.transactions.fee_coverage.FeePriority)
