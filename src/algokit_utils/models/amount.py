from __future__ import annotations

import algosdk
from typing_extensions import Self

__all__ = ["AlgoAmount"]


class AlgoAmount:
    """Wrapper class to ensure safe, explicit conversion between µAlgo, Algo and numbers.

    :param amount: A dictionary containing either algos, algo, microAlgos, or microAlgo as key
                    and their corresponding value as an integer or Decimal.
    :raises ValueError: If an invalid amount format is provided.

    :example:
    >>> amount = AlgoAmount({"algos": 1})
    >>> amount = AlgoAmount({"microAlgos": 1_000_000})
    """

    def __init__(self, amount: dict[str, int]):
        if "microAlgos" in amount:
            self.amount_in_micro_algo = int(amount["microAlgos"])
        elif "microAlgo" in amount:
            self.amount_in_micro_algo = int(amount["microAlgo"])
        elif "algos" in amount:
            self.amount_in_micro_algo = algosdk.util.algos_to_microalgos(float(amount["algos"]))
        elif "algo" in amount:
            self.amount_in_micro_algo = algosdk.util.algos_to_microalgos(float(amount["algo"]))
        else:
            raise ValueError("Invalid amount provided")

    @property
    def micro_algos(self) -> int:
        """Return the amount as a number in µAlgo.

        :returns: The amount in µAlgo.
        """
        return self.amount_in_micro_algo

    @property
    def micro_algo(self) -> int:
        """Return the amount as a number in µAlgo.

        :returns: The amount in µAlgo.
        """
        return self.amount_in_micro_algo

    @property
    def algos(self) -> int:
        """Return the amount as a number in Algo.

        :returns: The amount in Algo.
        """
        return algosdk.util.microalgos_to_algos(self.amount_in_micro_algo)  # type: ignore[no-any-return]

    @property
    def algo(self) -> int:
        """Return the amount as a number in Algo.

        :returns: The amount in Algo.
        """
        return algosdk.util.microalgos_to_algos(self.amount_in_micro_algo)  # type: ignore[no-any-return]

    @staticmethod
    def from_algos(amount: int) -> AlgoAmount:
        """Create an AlgoAmount object representing the given number of Algo.

        :param amount: The amount in Algo.
        :returns: An AlgoAmount instance.

        :example:
        >>> amount = AlgoAmount.from_algos(1)
        """
        return AlgoAmount({"algos": amount})

    @staticmethod
    def from_algo(amount: int) -> AlgoAmount:
        """Create an AlgoAmount object representing the given number of Algo.

        :param amount: The amount in Algo.
        :returns: An AlgoAmount instance.

        :example:
        >>> amount = AlgoAmount.from_algo(1)
        """
        return AlgoAmount({"algo": amount})

    @staticmethod
    def from_micro_algos(amount: int) -> AlgoAmount:
        """Create an AlgoAmount object representing the given number of µAlgo.

        :param amount: The amount in µAlgo.
        :returns: An AlgoAmount instance.

        :example:
        >>> amount = AlgoAmount.from_micro_algos(1_000_000)
        """
        return AlgoAmount({"microAlgos": amount})

    @staticmethod
    def from_micro_algo(amount: int) -> AlgoAmount:
        """Create an AlgoAmount object representing the given number of µAlgo.

        :param amount: The amount in µAlgo.
        :returns: An AlgoAmount instance.

        :example:
        >>> amount = AlgoAmount.from_micro_algo(1_000_000)
        """
        return AlgoAmount({"microAlgo": amount})

    def __str__(self) -> str:
        return f"{self.micro_algo:,} µALGO"

    def __int__(self) -> int:
        return self.micro_algos

    def __add__(self, other: AlgoAmount) -> AlgoAmount:
        if isinstance(other, AlgoAmount):
            total_micro_algos = self.micro_algos + other.micro_algos
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'AlgoAmount' and '{type(other).__name__}'")
        return AlgoAmount.from_micro_algos(total_micro_algos)

    def __radd__(self, other: AlgoAmount) -> AlgoAmount:
        return self.__add__(other)

    def __iadd__(self, other: AlgoAmount) -> Self:
        if isinstance(other, AlgoAmount):
            self.amount_in_micro_algo += other.micro_algos
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
            total_micro_algos = self.micro_algos - other.micro_algos
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'AlgoAmount' and '{type(other).__name__}'")
        return AlgoAmount.from_micro_algos(total_micro_algos)

    def __rsub__(self, other: int) -> AlgoAmount:
        if isinstance(other, (int)):
            total_micro_algos = int(other) - self.micro_algos
            return AlgoAmount.from_micro_algos(total_micro_algos)
        raise TypeError(f"Unsupported operand type(s) for -: '{type(other).__name__}' and 'AlgoAmount'")

    def __isub__(self, other: AlgoAmount) -> Self:
        if isinstance(other, AlgoAmount):
            self.amount_in_micro_algo -= other.micro_algos
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'AlgoAmount' and '{type(other).__name__}'")
        return self
