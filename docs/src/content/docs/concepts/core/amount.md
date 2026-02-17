---
title: "Algo amount handling"
description: "Algo amount handling is one of the core capabilities provided by AlgoKit Utils. It allows you to reliably and tersely specify amounts of microAlgo and Algo and safely convert between them."
---

Algo amount handling is one of the core capabilities provided by AlgoKit Utils. It allows you to reliably and tersely specify amounts of microAlgo and Algo and safely convert between them.

Any AlgoKit Utils function that needs an Algo amount will take an `AlgoAmount` object, which ensures that there is never any confusion about what value is being passed around. You can safely and explicitly convert to microAlgo or Algo when needed.

To see some usage examples check out the `automated tests`. Alternatively, you see the `reference documentation` for `AlgoAmount`.

## `AlgoAmount`

The `AlgoAmount` class provides a safe wrapper around an underlying amount of microAlgo where any value entering or existing the `AlgoAmount` class must be explicitly stated to be in microAlgo or Algo. This makes it much safer to handle Algo amounts rather than passing them around as raw numbers where it's easy to make a (potentially costly!) mistake and not perform a conversion when one is needed (or perform one when it shouldn't be!).

To import the AlgoAmount class you can access it via:

```python
from algokit_utils import AlgoAmount
```

### Creating an `AlgoAmount`

There are a few ways to create an `AlgoAmount`:

- Algo
  - Constructor: `AlgoAmount(algo=10)`
  - Static helper: `AlgoAmount.from_algo(10)`
- microAlgo
  - Constructor: `AlgoAmount(micro_algo=10_000)`
  - Static helper: `AlgoAmount.from_micro_algo(10_000)`

### Extracting a value from `AlgoAmount`

The `AlgoAmount` class has properties to return Algo and microAlgo:

- `amount.algo` - Returns the value in Algo
- `amount.micro_algo` - Returns the value in microAlgo

`AlgoAmount` will coerce to an integer automatically (in microAlgo) when using `int(amount)`.

`AlgoAmount` objects support comparison operators (`==`, `!=`, `<`, `<=`, `>`, `>=`) against other `AlgoAmount` instances or plain `int` values (treated as microAlgo).

You can also call `str(amount)` or use an `AlgoAmount` directly in string interpolation to convert it to a nice user-facing formatted amount expressed in microAlgo.

### Convenience functions

There are also standalone convenience functions for creating `AlgoAmount` instances:

```python
from algokit_utils import algo, micro_algo

amount1 = algo(1)            # equivalent to AlgoAmount.from_algo(1)
amount2 = micro_algo(1_000)  # equivalent to AlgoAmount.from_micro_algo(1_000)
```

### Arithmetic operations

`AlgoAmount` supports arithmetic operations with other `AlgoAmount` instances or plain `int` values (treated as microAlgo):

```python
a = AlgoAmount.from_algo(1)
b = AlgoAmount.from_algo(2)

# Addition and subtraction (AlgoAmount or int)
c = a + b           # AlgoAmount(micro_algo=3_000_000)
d = b - a           # AlgoAmount(micro_algo=1_000_000)

# Multiplication and division (int only)
e = a * 3           # AlgoAmount(micro_algo=3_000_000)
f = b / 2           # AlgoAmount(micro_algo=1_000_000)
```
