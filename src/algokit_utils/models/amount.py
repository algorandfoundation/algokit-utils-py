from decimal import Decimal
from functools import total_ordering
from typing import overload

from typing_extensions import Self

from algokit_common import MICROALGOS_TO_ALGOS_RATIO

__all__ = ["ALGORAND_MIN_TX_FEE", "AlgoAmount", "algo", "micro_algo", "transaction_fees"]


@total_ordering
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
            self.amount_in_micro_algo = int(algo * MICROALGOS_TO_ALGOS_RATIO)
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
        return Decimal(self.amount_in_micro_algo) / Decimal(MICROALGOS_TO_ALGOS_RATIO)

    @staticmethod
    def from_algo(amount: int | Decimal) -> "AlgoAmount":
        """Create an AlgoAmount object representing the given number of Algo.

        :param amount: The amount in Algo.
        :returns: An AlgoAmount instance.

        :example:
            >>> amount = AlgoAmount.from_algo(1)
        """
        return AlgoAmount(algo=amount)

    @staticmethod
    def from_micro_algo(amount: int) -> "AlgoAmount":
        """Create an AlgoAmount object representing the given number of µAlgo.

        :param amount: The amount in µAlgo.
        :returns: An AlgoAmount instance.

        :example:
            >>> amount = AlgoAmount.from_micro_algo(1_000_000)
        """
        return AlgoAmount(micro_algo=amount)

    def _coerce_micro_algos(self, other: object, op: str, *, allow_int: bool = False) -> int:
        if isinstance(other, AlgoAmount):
            return other.micro_algo
        if allow_int and isinstance(other, int):
            return int(other)
        raise TypeError(f"Unsupported operand type(s) for {op}: 'AlgoAmount' and '{type(other).__name__}'")

    def _coerce_int_scalar(self, other: object, op: str) -> int:
        if isinstance(other, int):
            return int(other)
        raise TypeError(f"Unsupported operand type(s) for {op}: 'AlgoAmount' and '{type(other).__name__}'")

    def __str__(self) -> str:
        return f"{self.micro_algo:,} µALGO"

    def __int__(self) -> int:
        return self.micro_algo

    def __add__(self, other: object) -> "AlgoAmount":
        total_micro_algos = self.micro_algo + self._coerce_micro_algos(other, "+", allow_int=True)
        return AlgoAmount.from_micro_algo(total_micro_algos)

    def __radd__(self, other: object) -> "AlgoAmount":
        return self.__add__(other)

    def __iadd__(self, other: object) -> Self:
        self.amount_in_micro_algo += self._coerce_micro_algos(other, "+", allow_int=True)
        return self

    def __eq__(self, other: object) -> bool:
        try:
            return self.amount_in_micro_algo == self._coerce_micro_algos(other, "==", allow_int=True)
        except TypeError:
            return False

    def __lt__(self, other: object) -> bool:
        other_micro_algos = self._coerce_micro_algos(other, "<", allow_int=True)
        return self.amount_in_micro_algo < other_micro_algos

    def __sub__(self, other: object) -> "AlgoAmount":
        total_micro_algos = self.micro_algo - self._coerce_micro_algos(other, "-", allow_int=True)
        return AlgoAmount.from_micro_algo(total_micro_algos)

    def __rsub__(self, other: object) -> "AlgoAmount":
        total_micro_algos = self._coerce_micro_algos(other, "-", allow_int=True) - self.micro_algo
        return AlgoAmount.from_micro_algo(total_micro_algos)

    def __isub__(self, other: object) -> Self:
        self.amount_in_micro_algo -= self._coerce_micro_algos(other, "-", allow_int=True)
        return self

    def __mul__(self, other: object) -> "AlgoAmount":
        factor = self._coerce_int_scalar(other, "*")
        return AlgoAmount.from_micro_algo(self.micro_algo * factor)

    def __rmul__(self, other: object) -> "AlgoAmount":
        return self.__mul__(other)

    def __truediv__(self, other: object) -> "AlgoAmount":
        divisor = self._coerce_int_scalar(other, "/")
        if divisor == 0:
            raise ZeroDivisionError("division by zero")
        return AlgoAmount.from_micro_algo(self.micro_algo // divisor)

    def __rtruediv__(self, other: object) -> Decimal:
        numerator = self._coerce_int_scalar(other, "/")
        if self.micro_algo == 0:
            raise ZeroDivisionError("division by zero")
        return Decimal(numerator) / Decimal(self.micro_algo)

    def __floordiv__(self, other: object) -> "AlgoAmount":
        divisor = self._coerce_int_scalar(other, "//")
        if divisor == 0:
            raise ZeroDivisionError("division by zero")
        return AlgoAmount.from_micro_algo(self.micro_algo // divisor)

    def __rfloordiv__(self, other: object) -> Decimal:
        numerator = self._coerce_int_scalar(other, "//")
        if self.micro_algo == 0:
            raise ZeroDivisionError("division by zero")
        return Decimal(numerator // self.micro_algo)


# Helper functions
def algo(algo: int) -> "AlgoAmount":
    """Create an AlgoAmount object representing the given number of Algo.

    :param algo: The number of Algo to create an AlgoAmount object for.
    :return: An AlgoAmount object representing the given number of Algo.
    """
    return AlgoAmount.from_algo(algo)


def micro_algo(micro_algo: int) -> "AlgoAmount":
    """Create an AlgoAmount object representing the given number of µAlgo.

    :param micro_algo: The number of µAlgo to create an AlgoAmount object for.
    :return: An AlgoAmount object representing the given number of µAlgo.
    """
    return AlgoAmount.from_micro_algo(micro_algo)


ALGORAND_MIN_TX_FEE = micro_algo(1_000)


def transaction_fees(number_of_transactions: int) -> "AlgoAmount":
    """Calculate the total transaction fees for a given number of transactions.

    :param number_of_transactions: The number of transactions to calculate the fees for.
    :return: The total transaction fees.
    """

    total_micro_algos = number_of_transactions * ALGORAND_MIN_TX_FEE.micro_algo
    return AlgoAmount.from_micro_algo(total_micro_algos)
