# algokit_utils.errors.logic_error

## Exceptions

| [`LogicError`](#algokit_utils.errors.logic_error.LogicError)   | Common base class for all non-exit exceptions.   |
|----------------------------------------------------------------|--------------------------------------------------|

## Classes

| [`LogicErrorData`](#algokit_utils.errors.logic_error.LogicErrorData)   | dict() -> new empty dictionary   |
|------------------------------------------------------------------------|----------------------------------|

## Functions

| [`parse_logic_error`](#algokit_utils.errors.logic_error.parse_logic_error)(→ LogicErrorData | None)   |    |
|-------------------------------------------------------------------------------------------------------|----|

## Module Contents

### *class* algokit_utils.errors.logic_error.LogicErrorData

Bases: `TypedDict`

dict() -> new empty dictionary
dict(mapping) -> new dictionary initialized from a mapping object’s

> (key, value) pairs

dict(iterable) -> new dictionary initialized as if via:
: d = {}
  for k, v in iterable:
  <br/>
  > d[k] = v

dict(

```
**
```

kwargs) -> new dictionary initialized with the name=value pairs
: in the keyword argument list.  For example:  dict(one=1, two=2)

#### transaction_id *: str*

#### message *: str*

#### pc *: int*

### algokit_utils.errors.logic_error.parse_logic_error(error_str: str) → [LogicErrorData](#algokit_utils.errors.logic_error.LogicErrorData) | None

### *exception* algokit_utils.errors.logic_error.LogicError(\*, logic_error_str: str, program: str, source_map: AlgoSourceMap | None, transaction_id: str, message: str, pc: int, logic_error: Exception | None = None, traces: list[[algokit_utils.models.simulate.SimulationTrace](../../models/simulate/index.md#algokit_utils.models.simulate.SimulationTrace)] | None = None, get_line_for_pc: collections.abc.Callable[[int], int | None] | None = None)

Bases: `Exception`

Common base class for all non-exit exceptions.

#### logic_error *= None*

#### logic_error_str

#### source_map

#### lines

#### transaction_id

#### message

#### pc

#### traces *= None*

#### line_no

#### trace(lines: int = 5) → str
