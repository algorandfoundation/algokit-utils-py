from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar


class FeeDeltaType(Enum):
    """Describes the type of fee delta"""

    DEFICIT = auto()
    SURPLUS = auto()


@dataclass(slots=True, frozen=True)
class FeeDelta:
    """Represents a difference between required and provided fee amounts."""

    type: FeeDeltaType
    data: int

    @staticmethod
    def from_int(value: int) -> "FeeDelta | None":
        if value > 0:
            return FeeDelta(FeeDeltaType.DEFICIT, value)
        if value < 0:
            return FeeDelta(FeeDeltaType.SURPLUS, -value)
        return None

    @staticmethod
    def add(lhs: "FeeDelta | None", rhs: "FeeDelta | None") -> "FeeDelta | None":
        if lhs is None:
            return rhs
        if rhs is None:
            return lhs
        return FeeDelta.from_int(FeeDelta.to_int(lhs) + FeeDelta.to_int(rhs))

    @staticmethod
    def to_int(delta: "FeeDelta") -> int:
        return delta.data if delta.type is FeeDeltaType.DEFICIT else -delta.data

    @staticmethod
    def amount(delta: "FeeDelta") -> int:
        return delta.data

    @staticmethod
    def is_deficit(delta: "FeeDelta") -> bool:
        return delta.type is FeeDeltaType.DEFICIT

    @staticmethod
    def is_surplus(delta: "FeeDelta") -> bool:
        return delta.type is FeeDeltaType.SURPLUS


@dataclass(slots=True, frozen=True, order=True)
class FeePriority:
    """Priority wrapper used when deciding which transactions need additional fees applied first."""

    priority_level: int
    deficit_amount: int
    Covered: ClassVar["FeePriority"]
    ModifiableDeficit: ClassVar[Callable[[int], "FeePriority"]]
    ImmutableDeficit: ClassVar[Callable[[int], "FeePriority"]]

    @staticmethod
    def covered() -> "FeePriority":
        return FeePriority(0, 0)

    @staticmethod
    def modifiable_deficit(amount: int) -> "FeePriority":
        return FeePriority(1, amount)

    @staticmethod
    def immutable_deficit(amount: int) -> "FeePriority":
        return FeePriority(2, amount)


FeePriority.Covered = FeePriority.covered()
FeePriority.ModifiableDeficit = staticmethod(FeePriority.modifiable_deficit)
FeePriority.ImmutableDeficit = staticmethod(FeePriority.immutable_deficit)
