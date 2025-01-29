from typing import NoReturn


def deprecated_import_error(old_path: str, new_path: str) -> NoReturn:
    """Helper to create consistent deprecation error messages"""
    raise ImportError(
        f"WARNING: The module '{old_path}' has been removed in algokit-utils v3. "
        f"Please update your imports to use '{new_path}' instead. "
        "See the migration guide for more details: "
        "https://github.com/algorandfoundation/algokit-utils-py/blob/main/docs/source/v3-migration-guide.md"
    )


def handle_getattr(name: str) -> NoReturn:
    param_mappings = {
        "ClientManager": "algokit_utils.ClientManager",
        "AlgorandClient": "algokit_utils.AlgorandClient",
        "AlgoSdkClients": "algokit_utils.AlgoSdkClients",
        "AccountManager": "algokit_utils.AccountManager",
        "PayParams": "algokit_utils.transactions.PaymentParams",
        "AlgokitComposer": "algokit_utils.TransactionComposer",
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
        deprecated_import_error(f"algokit_utils.beta.{name}", param_mappings[name])

    raise AttributeError(f"module 'algokit_utils.beta' has no attribute '{name}'")
