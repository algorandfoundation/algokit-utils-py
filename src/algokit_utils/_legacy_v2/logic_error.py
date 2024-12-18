from typing_extensions import deprecated

from algokit_utils.errors.logic_error import LogicError as NewLogicError
from algokit_utils.errors.logic_error import parse_logic_error

__all__ = [
    "LogicError",
    "parse_logic_error",
]


@deprecated("Use algokit_utils.models.error.LogicError instead")
class LogicError(NewLogicError):
    pass
