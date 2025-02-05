from __future__ import annotations

from decimal import Decimal
from typing import overload

import algosdk
from typing_extensions import Self

__all__ = ["ALGORAND_MIN_TX_FEE", "AlgoAmount", "algo", "micro_algo", "transaction_fees"]


class AlgoAmount:
    """Wrapper class to ensure safe, explicit conversion between µAlgo, Algo and numbers.

    :example:
        >>> amount = AlgoAmount(algo=1)
        >>> amount = AlgoAmount.from_algo(1)
        >>> amount = AlgoAmount(micro_algo=1_000_000)
        >>> amount = AlgoAmount.from_micro_algo(1_000_000)
    """

    @overload
    def __init__(self, *, micro_algo: int) -> None: ...

    @overload
    def __init__(self, *, algo: int | Decimal) -> None: ...

    def __init__(
        self,
        *,
        micro_algo: int | None = None,
        algo: int | Decimal | None = None,
    ):
        if micro_algo is None and algo is None:
            raise ValueError("No amount provided")

        if micro_algo is not None:
            self.amount_in_micro_algo = int(micro_algo)
        elif algo is not None:
            self.amount_in_micro_algo = int(algo * algosdk.constants.MICROALGOS_TO_ALGOS_RATIO)
        else:
            raise ValueError("Invalid amount provided")

    @property
    def micro_algo(self) -> int:
        """Return the amount as a number in µAlgo.

        :returns: The amount in µAlgo.
        """
        return self.amount_in_micro_algo

    @property
    def algo(self) -> Decimal:
        """Return the amount as a number in Algo.

        :returns: The amount in Algo.
        """
        return algosdk.util.microalgos_to_algos(self.amount_in_micro_algo)  # type: ignore[no-any-return]

    @staticmethod
    def from_algo(amount: int | Decimal) -> AlgoAmount:
        """Create an AlgoAmount object representing the given number of Algo.

        :param amount: The amount in Algo.
        :returns: An AlgoAmount instance.

        :example:
            >>> amount = AlgoAmount.from_algo(1)
        """
        return AlgoAmount(algo=amount)

    @staticmethod
    def from_micro_algo(amount: int) -> AlgoAmount:
        """Create an AlgoAmount object representing the given number of µAlgo.

        :param amount: The amount in µAlgo.
        :returns: An AlgoAmount instance.

        :example:
            >>> amount = AlgoAmount.from_micro_algo(1_000_000)
        """
        return AlgoAmount(micro_algo=amount)

    def __str__(self) -> str:
        return f"{self.micro_algo:,} µALGO"

    def __int__(self) -> int:
        return self.micro_algo

    def __add__(self, other: AlgoAmount) -> AlgoAmount:
        if isinstance(other, AlgoAmount):
            total_micro_algos = self.micro_algo + other.micro_algo
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'AlgoAmount' and '{type(other).__name__}'")
        return AlgoAmount.from_micro_algo(total_micro_algos)

    def __radd__(self, other: AlgoAmount) -> AlgoAmount:
        return self.__add__(other)

    def __iadd__(self, other: AlgoAmount) -> Self:
        if isinstance(other, AlgoAmount):
            self.amount_in_micro_algo += other.micro_algo
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'AlgoAmount' and '{type(other).__name__}'")
        return self

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo == other.amount_in_micro_algo
        elif isinstance(other, int):
            return self.amount_in_micro_algo == int(other)
        raise TypeError(f"Unsupported operand type(s) for ==: 'AlgoAmount' and '{type(other).__name__}'")

    def __ne__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo != other.amount_in_micro_algo
        elif isinstance(other, int):
            return self.amount_in_micro_algo != int(other)
        raise TypeError(f"Unsupported operand type(s) for !=: 'AlgoAmount' and '{type(other).__name__}'")

    def __lt__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo < other.amount_in_micro_algo
        elif isinstance(other, int):
            return self.amount_in_micro_algo < int(other)
        raise TypeError(f"Unsupported operand type(s) for <: 'AlgoAmount' and '{type(other).__name__}'")

    def __le__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo <= other.amount_in_micro_algo
        elif isinstance(other, int):
            return self.amount_in_micro_algo <= int(other)
        raise TypeError(f"Unsupported operand type(s) for <=: 'AlgoAmount' and '{type(other).__name__}'")

    def __gt__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo > other.amount_in_micro_algo
        elif isinstance(other, int):
            return self.amount_in_micro_algo > int(other)
        raise TypeError(f"Unsupported operand type(s) for >: 'AlgoAmount' and '{type(other).__name__}'")

    def __ge__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo >= other.amount_in_micro_algo
        elif isinstance(other, int):
            return self.amount_in_micro_algo >= int(other)
        raise TypeError(f"Unsupported operand type(s) for >=: 'AlgoAmount' and '{type(other).__name__}'")

    def __sub__(self, other: AlgoAmount) -> AlgoAmount:
        if isinstance(other, AlgoAmount):
            total_micro_algos = self.micro_algo - other.micro_algo
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'AlgoAmount' and '{type(other).__name__}'")
        return AlgoAmount.from_micro_algo(total_micro_algos)

    def __rsub__(self, other: int) -> AlgoAmount:
        if isinstance(other, (int)):
            total_micro_algos = int(other) - self.micro_algo
            return AlgoAmount.from_micro_algo(total_micro_algos)
        raise TypeError(f"Unsupported operand type(s) for -: '{type(other).__name__}' and 'AlgoAmount'")

    def __isub__(self, other: AlgoAmount) -> Self:
        if isinstance(other, AlgoAmount):
            self.amount_in_micro_algo -= other.micro_algo
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'AlgoAmount' and '{type(other).__name__}'")
        return self


# Helper functions
def algo(algo: int) -> AlgoAmount:
    """Create an AlgoAmount object representing the given number of Algo.

    :param algo: The number of Algo to create an AlgoAmount object for.
    :return: An AlgoAmount object representing the given number of Algo.
    """
    return AlgoAmount.from_algo(algo)


def micro_algo(micro_algo: int) -> AlgoAmount:
    """Create an AlgoAmount object representing the given number of µAlgo.

    :param micro_algo: The number of µAlgo to create an AlgoAmount object for.
    :return: An AlgoAmount object representing the given number of µAlgo.
    """
    return AlgoAmount.from_micro_algo(micro_algo)


ALGORAND_MIN_TX_FEE = micro_algo(1_000)


def transaction_fees(number_of_transactions: int) -> AlgoAmount:
    """Calculate the total transaction fees for a given number of transactions.

    :param number_of_transactions: The number of transactions to calculate the fees for.
    :return: The total transaction fees.
    """

    total_micro_algos = number_of_transactions * ALGORAND_MIN_TX_FEE.micro_algo
    return AlgoAmount.from_micro_algo(total_micro_algos)
