import warnings

warnings.warn(
    "The legacy v2 network clients module is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils._legacy_v2.network_clients import *  # noqa: F403, E402
