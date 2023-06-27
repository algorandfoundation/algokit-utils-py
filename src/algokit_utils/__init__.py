import typing
import warnings

from algokit_utils._ensure_funded import EnsureBalanceParameters, ensure_funded
from algokit_utils._transfer import (
    TransferParameters,
    transfer,
)
from algokit_utils.account import (
    create_kmd_wallet_account,
    get_account,
    get_account_from_mnemonic,
    get_dispenser_account,
    get_kmd_wallet_account,
    get_localnet_default_account,
    get_or_create_kmd_wallet_account,
)
from algokit_utils.application_client import (
    ApplicationClient,
    Program,
    execute_atc_with_logic_error,
    get_next_version,
    get_sender_from_signer,
    num_extra_program_pages,
)
from algokit_utils.application_specification import (
    ApplicationSpecification,
    AppSpecStateDict,
    CallConfig,
    DefaultArgumentDict,
    DefaultArgumentType,
    MethodConfigDict,
    MethodHints,
    OnCompleteActionName,
)
from algokit_utils.deploy import (
    DELETABLE_TEMPLATE_NAME,
    NOTE_PREFIX,
    UPDATABLE_TEMPLATE_NAME,
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
from algokit_utils.logic_error import LogicError
from algokit_utils.models import (
    ABIArgsDict,
    ABIMethod,
    ABITransactionResponse,
    Account,
    CreateCallParameters,
    CreateCallParametersDict,
    CreateTransactionParameters,
    OnCompleteCallParameters,
    OnCompleteCallParametersDict,
    TransactionParameters,
    TransactionParametersDict,
    TransactionResponse,
)
from algokit_utils.network_clients import (
    AlgoClientConfig,
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    get_indexer_client,
    get_kmd_client_from_algod_client,
    get_purestake_config,
    is_localnet,
    is_mainnet,
    is_testnet,
)

__all__ = [
    "create_kmd_wallet_account",
    "get_account_from_mnemonic",
    "get_or_create_kmd_wallet_account",
    "get_localnet_default_account",
    "get_dispenser_account",
    "get_kmd_wallet_account",
    "get_account",
    "UPDATABLE_TEMPLATE_NAME",
    "DELETABLE_TEMPLATE_NAME",
    "NOTE_PREFIX",
    "DeploymentFailedError",
    "AppReference",
    "AppDeployMetaData",
    "AppMetaData",
    "AppLookup",
    "get_creator_apps",
    "replace_template_variables",
    "ABIArgsDict",
    "ABICallArgs",
    "ABICallArgsDict",
    "ABICreateCallArgs",
    "ABICreateCallArgsDict",
    "ABIMethod",
    "CreateCallParameters",
    "CreateCallParametersDict",
    "CreateTransactionParameters",
    "DeployCallArgs",
    "DeployCreateCallArgs",
    "DeployCallArgsDict",
    "DeployCreateCallArgsDict",
    "OnCompleteCallParameters",
    "OnCompleteCallParametersDict",
    "TransactionParameters",
    "ApplicationClient",
    "DeployResponse",
    "OnUpdate",
    "OnSchemaBreak",
    "OperationPerformed",
    "TemplateValueDict",
    "TemplateValueMapping",
    "Program",
    "execute_atc_with_logic_error",
    "get_app_id_from_tx_id",
    "get_next_version",
    "get_sender_from_signer",
    "num_extra_program_pages",
    "AppSpecStateDict",
    "ApplicationSpecification",
    "CallConfig",
    "DefaultArgumentDict",
    "DefaultArgumentType",
    "MethodConfigDict",
    "OnCompleteActionName",
    "MethodHints",
    "LogicError",
    "ABITransactionResponse",
    "Account",
    "TransactionResponse",
    "AlgoClientConfig",
    "get_algod_client",
    "get_algonode_config",
    "get_default_localnet_config",
    "get_indexer_client",
    "get_kmd_client_from_algod_client",
    "get_purestake_config",
    "is_localnet",
    "is_mainnet",
    "is_testnet",
    "EnsureBalanceParameters",
    "TransferParameters",
    "ensure_funded",
    "transfer",
]


def __getattr__(name: str) -> typing.Any:  # noqa: ANN401
    # 1.3.0 backwards compatibility
    renamed = {
        "RawTransactionParameters": TransactionParameters,
        "CommonCallParameters": TransactionParameters,
        "CommonCallParametersDict": TransactionParametersDict,
    }
    if result := renamed.get(name):
        warnings.warn(
            f"{name} has been renamed to {result.__name__}",
            DeprecationWarning,
            stacklevel=1,
        )
        return result
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
