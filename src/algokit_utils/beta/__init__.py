from typing import Any, NoReturn


def _deprecated_import_error(old_path: str, new_path: str) -> NoReturn:
    """Helper to create consistent deprecation error messages"""
    raise ImportError(
        f"The module '{old_path}' has been moved in v3. "
        f"Please update your imports to use '{new_path}' instead. "
        "See the migration guide for more details: "
        "https://github.com/algorandfoundation/algokit-utils-py/blob/prerelease/ts-feature-parity/docs/migration-guide.md"
    )


class AlgorandClient:
    """@deprecated Use algokit_utils.clients.AlgorandClient instead"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        _deprecated_import_error("algokit_utils.beta.AlgorandClient", "algokit_utils.AlgorandClient")


class AlgokitComposer:
    """@deprecated Use algokit_utils.transactions.TransactionComposer instead"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        _deprecated_import_error("algokit_utils.beta.AlgokitComposer", "algokit_utils.TransactionComposer")


class AccountManager:
    """@deprecated Use algokit_utils.accounts.AccountManager instead"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        _deprecated_import_error("algokit_utils.beta.AccountManager", "algokit_utils.AccountManager")


class ClientManager:
    """@deprecated Use algokit_utils.clients.ClientManager instead"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        _deprecated_import_error("algokit_utils.beta.ClientManager", "algokit_utils.ClientManager")


# Re-export all the parameter classes with deprecation warnings
def __getattr__(name: str) -> Any:  # noqa: ANN401
    """Handle deprecated imports of parameter classes"""

    param_mappings = {
        # Transaction params
        "PayParams": "algokit_utils.transactions.PaymentParams",
        "AssetCreateParams": "algokit_utils.transactions.AssetCreateParams",
        "AssetConfigParams": "algokit_utils.transactions.AssetConfigParams",
        "AssetFreezeParams": "algokit_utils.transactions.AssetFreezeParams",
        "AssetDestroyParams": "algokit_utils.transactions.AssetDestroyParams",
        "AssetTransferParams": "algokit_utils.transactions.AssetTransferParams",
        "AssetOptInParams": "algokit_utils.transactions.AssetOptInParams",
        "AppCallParams": "algokit_utils.transactions.AppCallParams",
        "MethodCallParams": "algokit_utils.transactions.MethodCallParams",
        "OnlineKeyRegParams": "algokit_utils.transactions.OnlineKeyRegistrationParams",
    }

    if name in param_mappings:
        _deprecated_import_error(f"algokit_utils.beta.{name}", param_mappings[name])

    raise AttributeError(f"module 'algokit_utils.beta' has no attribute '{name}'")


# Clean up namespace to only show intended exports
__all__ = [
    "AccountManager",
    "AlgokitComposer",
    "AlgorandClient",
    "ClientManager",
]
