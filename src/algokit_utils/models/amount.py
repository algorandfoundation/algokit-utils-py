from __future__ import annotations

from decimal import Decimal

import algosdk
from typing_extensions import Self


class AlgoAmount:
    def __init__(self, amount: dict[str, int | Decimal]):
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
        return self.amount_in_micro_algo

    @property
    def micro_algo(self) -> int:
        return self.amount_in_micro_algo

    @property
    def algos(self) -> int | Decimal:
        return algosdk.util.microalgos_to_algos(self.amount_in_micro_algo)  # type: ignore[no-any-return]

    @property
    def algo(self) -> int | Decimal:
        return algosdk.util.microalgos_to_algos(self.amount_in_micro_algo)  # type: ignore[no-any-return]

    @staticmethod
    def from_algos(amount: int | Decimal) -> AlgoAmount:
        return AlgoAmount({"algos": amount})

    @staticmethod
    def from_algo(amount: int | Decimal) -> AlgoAmount:
        return AlgoAmount({"algo": amount})

    @staticmethod
    def from_micro_algos(amount: int | Decimal) -> AlgoAmount:
        return AlgoAmount({"microAlgos": amount})

    @staticmethod
    def from_micro_algo(amount: int | Decimal) -> AlgoAmount:
        return AlgoAmount({"microAlgo": amount})

    def __str__(self) -> str:
        """Return a string representation of the amount."""
        return f"{self.micro_algo:,} µALGO"

    def __int__(self) -> int:
        """Return the amount as an integer number of microAlgos."""
        return self.micro_algos

    def __add__(self, other: int | Decimal | AlgoAmount) -> AlgoAmount:
        if isinstance(other, AlgoAmount):
            total_micro_algos = self.micro_algos + other.micro_algos
        elif isinstance(other, (int | Decimal)):
            total_micro_algos = self.micro_algos + int(other)
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'AlgoAmount' and '{type(other).__name__}'")
        return AlgoAmount.from_micro_algos(total_micro_algos)

    def __radd__(self, other: int | Decimal) -> AlgoAmount:
        return self.__add__(other)

    def __iadd__(self, other: int | Decimal | AlgoAmount) -> Self:
        if isinstance(other, AlgoAmount):
            self.amount_in_micro_algo += other.micro_algos
        elif isinstance(other, (int | Decimal)):
            self.amount_in_micro_algo += int(other)
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'AlgoAmount' and '{type(other).__name__}'")
        return self

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo == other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo == int(other)
        raise TypeError(f"Unsupported operand type(s) for ==: 'AlgoAmount' and '{type(other).__name__}'")

    def __ne__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo != other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo != int(other)
        raise TypeError(f"Unsupported operand type(s) for !=: 'AlgoAmount' and '{type(other).__name__}'")

    def __lt__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo < other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo < int(other)
        raise TypeError(f"Unsupported operand type(s) for <: 'AlgoAmount' and '{type(other).__name__}'")

    def __le__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo <= other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo <= int(other)
        raise TypeError(f"Unsupported operand type(s) for <=: 'AlgoAmount' and '{type(other).__name__}'")

    def __gt__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo > other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo > int(other)
        raise TypeError(f"Unsupported operand type(s) for >: 'AlgoAmount' and '{type(other).__name__}'")

    def __ge__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo >= other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo >= int(other)
        raise TypeError(f"Unsupported operand type(s) for >=: 'AlgoAmount' and '{type(other).__name__}'")

    def __sub__(self, other: int | Decimal | AlgoAmount) -> AlgoAmount:
        if isinstance(other, AlgoAmount):
            total_micro_algos = self.micro_algos - other.micro_algos
        elif isinstance(other, (int | Decimal)):
            total_micro_algos = self.micro_algos - int(other)
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'AlgoAmount' and '{type(other).__name__}'")
        return AlgoAmount.from_micro_algos(total_micro_algos)

    def __rsub__(self, other: int | Decimal) -> AlgoAmount:
        if isinstance(other, (int | Decimal)):
            total_micro_algos = int(other) - self.micro_algos
            return AlgoAmount.from_micro_algos(total_micro_algos)
        raise TypeError(f"Unsupported operand type(s) for -: '{type(other).__name__}' and 'AlgoAmount'")

    def __isub__(self, other: int | Decimal | AlgoAmount) -> Self:
        if isinstance(other, AlgoAmount):
            self.amount_in_micro_algo -= other.micro_algos
        elif isinstance(other, (int | Decimal)):
            self.amount_in_micro_algo -= int(other)
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'AlgoAmount' and '{type(other).__name__}'")
        return self
