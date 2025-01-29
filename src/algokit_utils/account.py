import warnings

warnings.warn(
    """The legacy v2 account module is deprecated and will be removed in a future version.
    Use `SigningAccount` abstraction from `algokit_utils.models` instead or
    classes compliant with `TransactionSignerAccountProtocol` obtained from `AccountManager`.
""",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils._legacy_v2.account import *  # noqa: F403, E402
