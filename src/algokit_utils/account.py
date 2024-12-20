import warnings

warnings.warn(
    """The legacy v2 account module is deprecated and will be removed in a future version.
    Use `Account` abstraction from `algokit_utils.models` instead.
""",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils._legacy_v2.account import *  # noqa: F403, E402
