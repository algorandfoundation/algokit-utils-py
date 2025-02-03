# algokit_utils.models.amount

## Attributes

| [`ALGORAND_MIN_TX_FEE`](#algokit_utils.models.amount.ALGORAND_MIN_TX_FEE)   |    |
|-----------------------------------------------------------------------------|----|

## Classes

| [`AlgoAmount`](#algokit_utils.models.amount.AlgoAmount)   | Wrapper class to ensure safe, explicit conversion between µAlgo, Algo and numbers.   |
|-----------------------------------------------------------|--------------------------------------------------------------------------------------|

## Functions

| [`algo`](#algokit_utils.models.amount.algo)(→ AlgoAmount)                         | Create an AlgoAmount object representing the given number of Algo.       |
|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`micro_algo`](#algokit_utils.models.amount.micro_algo)(→ AlgoAmount)             | Create an AlgoAmount object representing the given number of µAlgo.      |
| [`transaction_fees`](#algokit_utils.models.amount.transaction_fees)(→ AlgoAmount) | Calculate the total transaction fees for a given number of transactions. |

## Module Contents

### *class* algokit_utils.models.amount.AlgoAmount(\*, micro_algos: int)

### *class* algokit_utils.models.amount.AlgoAmount(\*, micro_algo: int)

### *class* algokit_utils.models.amount.AlgoAmount(\*, algos: int | decimal.Decimal)

### *class* algokit_utils.models.amount.AlgoAmount(\*, algo: int | decimal.Decimal)

Wrapper class to ensure safe, explicit conversion between µAlgo, Algo and numbers.

* **Example:**

```pycon
>>> amount = AlgoAmount(algos=1)
>>> amount = AlgoAmount(algo=1)
>>> amount = AlgoAmount.from_algos(1)
>>> amount = AlgoAmount.from_algo(1)
>>> amount = AlgoAmount(micro_algos=1_000_000)
>>> amount = AlgoAmount(micro_algo=1_000_000)
>>> amount = AlgoAmount.from_micro_algos(1_000_000)
>>> amount = AlgoAmount.from_micro_algo(1_000_000)
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

### algokit_utils.models.amount.algo(algos: int) → [AlgoAmount](#algokit_utils.models.amount.AlgoAmount)

Create an AlgoAmount object representing the given number of Algo.

* **Parameters:**
  **algos** – The number of Algo to create an AlgoAmount object for.
* **Returns:**
  An AlgoAmount object representing the given number of Algo.

### algokit_utils.models.amount.micro_algo(microalgos: int) → [AlgoAmount](#algokit_utils.models.amount.AlgoAmount)

Create an AlgoAmount object representing the given number of µAlgo.

* **Parameters:**
  **microalgos** – The number of µAlgo to create an AlgoAmount object for.
* **Returns:**
  An AlgoAmount object representing the given number of µAlgo.

### algokit_utils.models.amount.ALGORAND_MIN_TX_FEE

### algokit_utils.models.amount.transaction_fees(number_of_transactions: int) → [AlgoAmount](#algokit_utils.models.amount.AlgoAmount)

Calculate the total transaction fees for a given number of transactions.

* **Parameters:**
  **number_of_transactions** – The number of transactions to calculate the fees for.
* **Returns:**
  The total transaction fees.
