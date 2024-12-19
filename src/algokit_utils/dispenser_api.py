import warnings

warnings.warn(
    "The legacy v2 dispenser api module is deprecated and will be removed in a future version. "
    "Import from 'algokit_utils.clients.dispenser_api_client' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils.clients.dispenser_api_client import *  # noqa: F403, E402
