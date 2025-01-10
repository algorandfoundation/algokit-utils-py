"""AlgoKit Python Utilities - a set of utilities for building solutions on Algorand

This module provides commonly used utilities and types at the root level for convenience.
For more specific functionality, import directly from the relevant submodules:

    from algokit_utils.accounts import KmdAccountManager
    from algokit_utils.applications import AppClient
    from algokit_utils.applications.app_spec import Arc52Contract
    etc.
"""

# Core types and utilities that are commonly used
from algokit_utils.models.account import Account
from algokit_utils.applications.app_manager import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME
from algokit_utils.errors.logic_error import LogicError
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.protocols import AlgorandClientProtocol

# Common managers/clients that are frequently used entry points
from algokit_utils.accounts.account_manager import AccountManager
from algokit_utils.applications.app_client import AppClient
from algokit_utils.applications.app_factory import AppFactory
from algokit_utils.assets.asset_manager import AssetManager
from algokit_utils.clients.client_manager import ClientManager
from algokit_utils.transactions.transaction_composer import TransactionComposer

# Commonly used constants
from algokit_utils.clients.dispenser_api_client import (
    DISPENSER_ACCESS_TOKEN_KEY,
    TestNetDispenserApiClient,
    DISPENSER_REQUEST_TIMEOUT,
)

# ==== LEGACY V2 SUPPORT BEGIN ====
# These imports are maintained for backwards compatibility
from algokit_utils._legacy_v2._ensure_funded import (
    EnsureBalanceParameters,
    EnsureFundedResponse,
    ensure_funded,
)
from algokit_utils._legacy_v2._transfer import (
    TransferAssetParameters,
    TransferParameters,
    transfer,
    transfer_asset,
)
from algokit_utils._legacy_v2.account import (
    create_kmd_wallet_account,
    get_account,
    get_account_from_mnemonic,
    get_dispenser_account,
    get_kmd_wallet_account,
    get_localnet_default_account,
    get_or_create_kmd_wallet_account,
)
from algokit_utils._legacy_v2.application_client import (
    ApplicationClient,
    execute_atc_with_logic_error,
    get_next_version,
    get_sender_from_signer,
    num_extra_program_pages,
)
from algokit_utils._legacy_v2.application_specification import (
    ApplicationSpecification,
    AppSpecStateDict,
    CallConfig,
    DefaultArgumentDict,
    DefaultArgumentType,
    MethodConfigDict,
    MethodHints,
    OnCompleteActionName,
)
from algokit_utils._legacy_v2.asset import opt_in, opt_out
from algokit_utils._legacy_v2.common import Program
from algokit_utils._legacy_v2.deploy import (
    NOTE_PREFIX,
    ABICallArgs,
    ABICallArgsDict,
    ABICreateCallArgs,
    ABICreateCallArgsDict,
    AppDeployMetaData,
    AppLookup,
    AppMetaData,
    AppReference,
    DeployCallArgs,
    DeployCallArgsDict,
    DeployCreateCallArgs,
    DeployCreateCallArgsDict,
    DeploymentFailedError,
    DeployResponse,
    OnSchemaBreak,
    OnUpdate,
    OperationPerformed,
    TemplateValueDict,
    TemplateValueMapping,
    get_app_id_from_tx_id,
    get_creator_apps,
    replace_template_variables,
)
from algokit_utils._legacy_v2.models import (
    ABIArgsDict,
    ABIMethod,
    ABITransactionResponse,
    CommonCallParameters,
    CommonCallParametersDict,
    CreateCallParameters,
    CreateCallParametersDict,
    CreateTransactionParameters,
    OnCompleteCallParameters,
    OnCompleteCallParametersDict,
    TransactionParameters,
    TransactionParametersDict,
    TransactionResponse,
)
from algokit_utils._legacy_v2.network_clients import (
    AlgoClientConfig,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    get_indexer_client,
    get_kmd_client_from_algod_client,
    is_localnet,
    is_mainnet,
    is_testnet,
)
# ==== LEGACY V2 SUPPORT END ====

# Debugging utilities
from algokit_utils._debugging import (
    PersistSourceMapInput,
    persist_sourcemaps,
    simulate_and_persist_response,
)

__all__ = [
    # Core types and utilities
    "Account",
    "LogicError",
    "AlgorandClient",
    "DELETABLE_TEMPLATE_NAME",
    "UPDATABLE_TEMPLATE_NAME",
    "AlgorandClientProtocol",
    # Common managers/clients
    "AccountManager",
    "AppClient",
    "AppFactory",
    "AssetManager",
    "ClientManager",
    "TransactionComposer",
    "TestNetDispenserApiClient",
    # Constants
    "DISPENSER_ACCESS_TOKEN_KEY",
    "DISPENSER_REQUEST_TIMEOUT",
    "NOTE_PREFIX",
    # Legacy v2 exports - maintained for backwards compatibility
    "ABIArgsDict",
    "ABICallArgs",
    "ABICallArgsDict",
    "ABICreateCallArgs",
    "ABICreateCallArgsDict",
    "ABIMethod",
    "ABITransactionResponse",
    "AlgoClientConfig",
    "AppDeployMetaData",
    "AppLookup",
    "AppMetaData",
    "AppReference",
    "AppSpecStateDict",
    "ApplicationClient",
    "ApplicationSpecification",
    "CallConfig",
    "CommonCallParameters",
    "CommonCallParametersDict",
    "CreateCallParameters",
    "CreateCallParametersDict",
    "CreateTransactionParameters",
    "DefaultArgumentDict",
    "DefaultArgumentType",
    "DeployCallArgs",
    "DeployCallArgsDict",
    "DeployCreateCallArgs",
    "DeployCreateCallArgsDict",
    "DeployResponse",
    "DeploymentFailedError",
    "EnsureBalanceParameters",
    "EnsureFundedResponse",
    "MethodConfigDict",
    "MethodHints",
    "OnCompleteActionName",
    "OnCompleteCallParameters",
    "OnCompleteCallParametersDict",
    "OnSchemaBreak",
    "OnUpdate",
    "OperationPerformed",
    "PersistSourceMapInput",
    "Program",
    "TemplateValueDict",
    "TemplateValueMapping",
    "TransactionParameters",
    "TransactionParametersDict",
    "TransactionResponse",
    "TransferAssetParameters",
    "TransferParameters",
    # Legacy v2 functions
    "create_kmd_wallet_account",
    "ensure_funded",
    "execute_atc_with_logic_error",
    "get_account",
    "get_account_from_mnemonic",
    "get_algod_client",
    "get_algonode_config",
    "get_app_id_from_tx_id",
    "get_creator_apps",
    "get_default_localnet_config",
    "get_dispenser_account",
    "get_indexer_client",
    "get_kmd_client_from_algod_client",
    "get_kmd_wallet_account",
    "get_localnet_default_account",
    "get_next_version",
    "get_or_create_kmd_wallet_account",
    "get_sender_from_signer",
    "is_localnet",
    "is_mainnet",
    "is_testnet",
    "num_extra_program_pages",
    "opt_in",
    "opt_out",
    "persist_sourcemaps",
    "replace_template_variables",
    "simulate_and_persist_response",
    "transfer",
    "transfer_asset",
]
