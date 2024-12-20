import warnings

warnings.warn(
    "The legacy v2 logic error module is deprecated and will be removed in a future version. "
    "Use 'from algokit_utils.errors import LogicError' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils.errors.logic_error import *  # noqa: F403, E402
