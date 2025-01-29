# algokit_utils.models.amount

## Classes

| [`AlgoAmount`](#algokit_utils.models.amount.AlgoAmount)   | Wrapper class to ensure safe, explicit conversion between µAlgo, Algo and numbers.   |
|-----------------------------------------------------------|--------------------------------------------------------------------------------------|

## Module Contents

### *class* algokit_utils.models.amount.AlgoAmount(amount: dict[str, int | decimal.Decimal])

Wrapper class to ensure safe, explicit conversion between µAlgo, Algo and numbers.

* **Parameters:**
  **amount** – A dictionary containing either algos, algo, microAlgos, or microAlgo as key
  and their corresponding value as an integer or Decimal.
* **Raises:**
  **ValueError** – If an invalid amount format is provided.
* **Example:**

```pycon
>>> amount = AlgoAmount({"algos": 1})
>>> amount = AlgoAmount({"microAlgos": 1_000_000})
```

#### *property* micro_algos *: int*

Return the amount as a number in µAlgo.

* **Returns:**
  The amount in µAlgo.

#### *property* micro_algo *: int*

Return the amount as a number in µAlgo.

* **Returns:**
  The amount in µAlgo.

#### *property* algos *: decimal.Decimal*

Return the amount as a number in Algo.

* **Returns:**
  The amount in Algo.

#### *property* algo *: decimal.Decimal*

Return the amount as a number in Algo.

* **Returns:**
  The amount in Algo.

#### *static* from_algos(amount: int | decimal.Decimal) → [AlgoAmount](#algokit_utils.models.amount.AlgoAmount)

Create an AlgoAmount object representing the given number of Algo.

* **Parameters:**
  **amount** – The amount in Algo.
* **Returns:**
  An AlgoAmount instance.
* **Example:**

```pycon
>>> amount = AlgoAmount.from_algos(1)
```

#### *static* from_algo(amount: int | decimal.Decimal) → [AlgoAmount](#algokit_utils.models.amount.AlgoAmount)

Create an AlgoAmount object representing the given number of Algo.

* **Parameters:**
  **amount** – The amount in Algo.
* **Returns:**
  An AlgoAmount instance.
* **Example:**

```pycon
>>> amount = AlgoAmount.from_algo(1)
```

#### *static* from_micro_algos(amount: int) → [AlgoAmount](#algokit_utils.models.amount.AlgoAmount)

Create an AlgoAmount object representing the given number of µAlgo.

* **Parameters:**
  **amount** – The amount in µAlgo.
* **Returns:**
  An AlgoAmount instance.
* **Example:**

```pycon
>>> amount = AlgoAmount.from_micro_algos(1_000_000)
```

#### *static* from_micro_algo(amount: int) → [AlgoAmount](#algokit_utils.models.amount.AlgoAmount)

Create an AlgoAmount object representing the given number of µAlgo.

* **Parameters:**
  **amount** – The amount in µAlgo.
* **Returns:**
  An AlgoAmount instance.
* **Example:**

```pycon
>>> amount = AlgoAmount.from_micro_algo(1_000_000)
```
