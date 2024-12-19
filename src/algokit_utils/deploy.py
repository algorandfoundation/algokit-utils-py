import warnings

warnings.warn(
    "The legacy v2 deploy module is deprecated and will be removed in a future version. "
    "Refer to `AppFactory` and `AppDeployer` abstractions from `algokit_utils` module instead.",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils._legacy_v2.deploy import *  # noqa: F403, E402
