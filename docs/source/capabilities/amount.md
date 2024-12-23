# Algo amount handling

Algo amount handling is one of the core capabilities provided by AlgoKit Utils. It allows you to reliably and tersely specify amounts of microAlgo and Algo and safely convert between them.

Any AlgoKit Utils function that needs an Algo amount will take an `AlgoAmount` object, which ensures that there is never any confusion about what value is being passed around. Whenever an AlgoKit Utils function calls into an underlying algosdk function, or if you need to take an `AlgoAmount` and pass it into an underlying algosdk function you can safely and explicitly convert to microAlgo or Algo.

To see some usage examples check out the automated tests in the repository. Alternatively, you can refer to the reference documentation for `AlgoAmount`.

## `AlgoAmount`

The `AlgoAmount` class provides a safe wrapper around an underlying amount of microAlgo where any value entering or exiting the `AlgoAmount` class must be explicitly stated to be in microAlgo or Algo. This makes it much safer to handle Algo amounts rather than passing them around as raw numbers where it's easy to make a (potentially costly!) mistake and not perform a conversion when one is needed (or perform one when it shouldn't be!).

To import the AlgoAmount class you can access it via:

```python
from algokit_utils.models import AlgoAmount
```

### Creating an `AlgoAmount`

There are several ways to create an `AlgoAmount`:

- Algo
  - Constructor: `AlgoAmount({"algo": 10})`
  - Static helper: `AlgoAmount.from_algo(10)`
  - Static helper (plural): `AlgoAmount.from_algos(10)`
- microAlgo
  - Constructor: `AlgoAmount({"microAlgo": 10_000})`
  - Static helper: `AlgoAmount.from_micro_algo(10_000)`
  - Static helper (plural): `AlgoAmount.from_micro_algos(10_000)`

### Extracting a value from `AlgoAmount`

The `AlgoAmount` class has properties to return Algo and microAlgo:

- `amount.algo` or `amount.algos` - Returns the value in Algo
- `amount.micro_algo` or `amount.micro_algos` - Returns the value in microAlgo

`AlgoAmount` will coerce to an integer automatically (in microAlgo) when using `int(amount)`, which allows you to use `AlgoAmount` objects in comparison operations such as `<` and `>=` etc.

You can also call `str(amount)` or use an `AlgoAmount` directly in string interpolation to convert it to a nice user-facing formatted amount expressed in microAlgo.

### Additional Features

The `AlgoAmount` class also supports:

- Arithmetic operations (`+`, `-`) with other `AlgoAmount` objects or integers
- Comparison operations (`<`, `<=`, `>`, `>=`, `==`, `!=`)
- In-place arithmetic (`+=`, `-=`)

Example usage:

```python
from algokit_utils.models import AlgoAmount

# Create amounts
amount1 = AlgoAmount.from_algo(1.5)  # 1.5 Algos
amount2 = AlgoAmount.from_micro_algos(500_000)  # 0.5 Algos

# Arithmetic
total = amount1 + amount2  # 2 Algos
difference = amount1 - amount2  # 1 Algo

# Comparisons
is_greater = amount1 > amount2  # True

# String representation
print(amount1)  # "1,500,000 µALGO"
```
