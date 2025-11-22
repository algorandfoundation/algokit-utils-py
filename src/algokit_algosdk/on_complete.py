from enum import IntEnum


class OnComplete(IntEnum):
    NoOpOC = 0
    OptInOC = 1
    CloseOutOC = 2
    ClearStateOC = 3
    UpdateApplicationOC = 4
    DeleteApplicationOC = 5


__all__ = ["OnComplete"]
