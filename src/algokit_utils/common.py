import warnings

warnings.warn(
    "The legacy v2 common module is deprecated and will be removed in a future version. "
    "Refer to `CompiledTeal` class from `algokit_utils` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils._legacy_v2.common import *  # noqa: F403, E402
