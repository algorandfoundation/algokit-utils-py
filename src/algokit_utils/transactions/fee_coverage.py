from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


class FeeDeltaType(Enum):
    """Represents the direction of a fee delta."""

    DEFICIT = auto()
    SURPLUS = auto()


@dataclass(frozen=True, slots=True)
class FeeDelta:
    """Encapsulates the delta between the required fee and the current fee."""

    kind: FeeDeltaType
    amount: int

    @staticmethod
    def from_int(value: int) -> FeeDelta | None:
        """Create a fee delta from an integer value."""
        if value > 0:
            return FeeDelta(FeeDeltaType.DEFICIT, value)
        if value < 0:
            return FeeDelta(FeeDeltaType.SURPLUS, -value)
        return None

    def to_int(self) -> int:
        """Convert the delta into a signed integer."""
        return self.amount if self.kind is FeeDeltaType.DEFICIT else -self.amount

    def is_deficit(self) -> bool:
        """Return True if the delta represents a deficit."""
        return self.kind is FeeDeltaType.DEFICIT

    def is_surplus(self) -> bool:
        """Return True if the delta represents a surplus."""
        return self.kind is FeeDeltaType.SURPLUS

    def add(self, other: FeeDelta) -> FeeDelta | None:
        """Add another fee delta to this one."""
        return FeeDelta.from_int(self.to_int() + other.to_int())


class FeePriority(Protocol):
    """Fee coverage priority contract."""

    def priority_type(self) -> int: ...

    def deficit_amount(self) -> int: ...

    def compare(self, other: FeePriority) -> int: ...


@dataclass(slots=True)
class CoveredPriority(FeePriority):
    """Priority given to transactions that are already covered."""

    def priority_type(self) -> int:
        return 0

    def deficit_amount(self) -> int:
        return 0

    def compare(self, other: FeePriority) -> int:
        return self.priority_type() - other.priority_type()


@dataclass(slots=True)
class ModifiableDeficitPriority(FeePriority):
    """Priority for transactions whose fees can still be modified."""

    deficit: int

    def priority_type(self) -> int:
        return 1

    def deficit_amount(self) -> int:
        return self.deficit

    def compare(self, other: FeePriority) -> int:
        type_diff = self.priority_type() - other.priority_type()
        if type_diff != 0:
            return type_diff
        if isinstance(other, ModifiableDeficitPriority):
            return self.deficit - other.deficit
        return 0


@dataclass(slots=True)
class ImmutableDeficitPriority(FeePriority):
    """Priority for transactions whose fees cannot be changed."""

    deficit: int

    def priority_type(self) -> int:
        return 2

    def deficit_amount(self) -> int:
        return self.deficit

    def compare(self, other: FeePriority) -> int:
        type_diff = self.priority_type() - other.priority_type()
        if type_diff != 0:
            return type_diff
        if isinstance(other, ImmutableDeficitPriority):
            return self.deficit - other.deficit
        return 0


class FeePriorities:
    """Factory helpers for fee priorities."""

    covered = CoveredPriority()

    @staticmethod
    def modifiable(deficit: int) -> ModifiableDeficitPriority:
        return ModifiableDeficitPriority(deficit)

    @staticmethod
    def immutable(deficit: int) -> ImmutableDeficitPriority:
        return ImmutableDeficitPriority(deficit)
