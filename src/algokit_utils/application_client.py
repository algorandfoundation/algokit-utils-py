import warnings

warnings.warn(
    """The legacy v2 application_client module is deprecated and will be removed in a future version.
    Use `AppClient` abstraction from `algokit_utils.applications` instead.
""",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils._legacy_v2.application_client import *  # noqa: F403, E402
