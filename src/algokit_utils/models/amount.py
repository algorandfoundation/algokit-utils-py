from __future__ import annotations

from decimal import Decimal

import algosdk


class AlgoAmount:
    def __init__(self, amount: dict[str, float | int | Decimal]):
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
    def algos(self) -> Decimal:
        return algosdk.util.microalgos_to_algos(self.amount_in_micro_algo)  # type: ignore[no-any-return]

    @property
    def algo(self) -> Decimal:
        return algosdk.util.microalgos_to_algos(self.amount_in_micro_algo)  # type: ignore[no-any-return]

    @staticmethod
    def from_algos(amount: float | Decimal) -> AlgoAmount:
        return AlgoAmount({"algos": amount})

    @staticmethod
    def from_algo(amount: float | Decimal) -> AlgoAmount:
        return AlgoAmount({"algo": amount})

    @staticmethod
    def from_micro_algos(amount: int) -> AlgoAmount:
        return AlgoAmount({"microAlgos": amount})

    @staticmethod
    def from_micro_algo(amount: int) -> AlgoAmount:
        return AlgoAmount({"microAlgo": amount})

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo == other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo == int(other)
        raise NotImplementedError

    def __ne__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo != other.amount_in_micro_algo
        elif isinstance(other, (int | Decimal)):
            return self.amount_in_micro_algo != int(other)
        raise NotImplementedError

    def __lt__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo < other.amount_in_micro_algo
        elif isinstance(other, (int | Decimal)):
            return self.amount_in_micro_algo < int(other)
        raise NotImplementedError

    def __le__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo <= other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo <= int(other)
        raise NotImplementedError

    def __gt__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo > other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo > int(other)
        raise NotImplementedError

    def __ge__(self, other: object) -> bool:
        if isinstance(other, AlgoAmount):
            return self.amount_in_micro_algo >= other.amount_in_micro_algo
        elif isinstance(other, int | Decimal):
            return self.amount_in_micro_algo >= int(other)
        raise NotImplementedError
