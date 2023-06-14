import base64
import dataclasses
import json
import logging
import re
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, TypeAlias, TypedDict

from algosdk import transaction
from algosdk.atomic_transaction_composer import AtomicTransactionComposer, TransactionSigner
from algosdk.logic import get_application_address
from algosdk.transaction import StateSchema

from algokit_utils.application_specification import (
    ApplicationSpecification,
    CallConfig,
    MethodConfigDict,
    OnCompleteActionName,
)
from algokit_utils.models import (
    ABIArgsDict,
    ABIMethod,
    Account,
    CreateCallParameters,
    TransactionResponse,
)

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient

    from algokit_utils.application_client import ApplicationClient


__all__ = [
    "UPDATABLE_TEMPLATE_NAME",
    "DELETABLE_TEMPLATE_NAME",
    "NOTE_PREFIX",
    "ABICallArgs",
    "ABICreateCallArgs",
    "ABICallArgsDict",
    "ABICreateCallArgsDict",
    "DeploymentFailedError",
    "AppReference",
    "AppDeployMetaData",
    "AppMetaData",
    "AppLookup",
    "DeployCallArgs",
    "DeployCreateCallArgs",
    "DeployCallArgsDict",
    "DeployCreateCallArgsDict",
    "Deployer",
    "DeployResponse",
    "OnUpdate",
    "OnSchemaBreak",
    "OperationPerformed",
    "TemplateValueDict",
    "TemplateValueMapping",
    "get_app_id_from_tx_id",
    "get_creator_apps",
    "replace_template_variables",
]

logger = logging.getLogger(__name__)

DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT = 1000
_UPDATABLE = "UPDATABLE"
_DELETABLE = "DELETABLE"
UPDATABLE_TEMPLATE_NAME = f"TMPL_{_UPDATABLE}"
"""Template variable name used to control if a smart contract is updatable or not at deployment"""
DELETABLE_TEMPLATE_NAME = f"TMPL_{_DELETABLE}"
"""Template variable name used to control if a smart contract is deletable or not at deployment"""
_TOKEN_PATTERN = re.compile(r"TMPL_[A-Z]+")
TemplateValue: TypeAlias = int | str | bytes
TemplateValueDict: TypeAlias = dict[str, TemplateValue]
"""Dictionary of `dict[str, int | str | bytes]` representing template variable names and values"""
TemplateValueMapping: TypeAlias = Mapping[str, TemplateValue]
"""Mapping of `str` to `int | str | bytes` representing template variable names and values"""

NOTE_PREFIX = "ALGOKIT_DEPLOYER:j"
"""ARC-0002 compliant note prefix for algokit_utils deployed applications"""
# This prefix is also used to filter for parsable transaction notes in get_creator_apps.
# However, as the note is base64 encoded first we need to consider it's base64 representation.
# When base64 encoding bytes, 3 bytes are stored in every 4 characters.
# So then we don't need to worry about the padding/changing characters of the prefix if it was followed by
# additional characters, assert the NOTE_PREFIX length is a multiple of 3.
assert len(NOTE_PREFIX) % 3 == 0


class DeploymentFailedError(Exception):
    pass


@dataclasses.dataclass
class AppReference:
    """Information about an Algorand app"""

    app_id: int
    app_address: str


@dataclasses.dataclass
class AppDeployMetaData:
    """Metadata about an application stored in a transaction note during creation.

    The note is serialized as JSON and prefixed with {py:data}`NOTE_PREFIX` and stored in the transaction note field
    as part of {py:meth}`ApplicationClient.deploy`
    """

    name: str
    version: str
    deletable: bool | None
    updatable: bool | None

    @staticmethod
    def from_json(value: str) -> "AppDeployMetaData":
        json_value: dict = json.loads(value)
        json_value.setdefault("deletable", None)
        json_value.setdefault("updatable", None)
        return AppDeployMetaData(**json_value)

    @classmethod
    def from_b64(cls: type["AppDeployMetaData"], b64: str) -> "AppDeployMetaData":
        return cls.decode(base64.b64decode(b64))

    @classmethod
    def decode(cls: type["AppDeployMetaData"], value: bytes) -> "AppDeployMetaData":
        note = value.decode("utf-8")
        assert note.startswith(NOTE_PREFIX)
        return cls.from_json(note[len(NOTE_PREFIX) :])

    def encode(self) -> bytes:
        json_str = json.dumps(self.__dict__)
        return f"{NOTE_PREFIX}{json_str}".encode()


@dataclasses.dataclass
class AppMetaData(AppReference, AppDeployMetaData):
    """Metadata about a deployed app"""

    created_round: int
    updated_round: int
    created_metadata: AppDeployMetaData
    deleted: bool


@dataclasses.dataclass
class AppLookup:
    """Cache of {py:class}`AppMetaData` for a specific `creator`

    Can be used as an argument to {py:class}`ApplicationClient` to reduce the number of calls when deploying multiple
    apps or discovering multiple app_ids
    """

    creator: str
    apps: dict[str, AppMetaData] = dataclasses.field(default_factory=dict)


def _sort_by_round(txn: dict) -> tuple[int, int]:
    confirmed = txn["confirmed-round"]
    offset = txn["intra-round-offset"]
    return confirmed, offset


def _parse_note(metadata_b64: str | None) -> AppDeployMetaData | None:
    if not metadata_b64:
        return None
    # noinspection PyBroadException
    try:
        return AppDeployMetaData.from_b64(metadata_b64)
    except Exception:
        return None


def get_creator_apps(indexer: "IndexerClient", creator_account: Account | str) -> AppLookup:
    """Returns a mapping of Application names to {py:class}`AppMetaData` for all Applications created by specified
    creator that have a transaction note containing {py:class}`AppDeployMetaData`
    """
    apps: dict[str, AppMetaData] = {}

    creator_address = creator_account if isinstance(creator_account, str) else creator_account.address
    token = None
    # TODO: paginated indexer call instead of N + 1 calls
    while True:
        response = indexer.lookup_account_application_by_creator(
            creator_address, limit=DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT, next_page=token
        )  # type: ignore[no-untyped-call]
        if "message" in response:  # an error occurred
            raise Exception(f"Error querying applications for {creator_address}: {response}")
        for app in response["applications"]:
            app_id = app["id"]
            app_created_at_round = app["created-at-round"]
            app_deleted = app.get("deleted", False)
            search_transactions_response = indexer.search_transactions(
                min_round=app_created_at_round,
                txn_type="appl",
                application_id=app_id,
                address=creator_address,
                address_role="sender",
                note_prefix=NOTE_PREFIX.encode("utf-8"),
            )  # type: ignore[no-untyped-call]
            transactions: list[dict] = search_transactions_response["transactions"]
            if not transactions:
                continue

            created_transaction = next(
                t
                for t in transactions
                if t["application-transaction"]["application-id"] == 0 and t["sender"] == creator_address
            )

            transactions.sort(key=_sort_by_round, reverse=True)
            latest_transaction = transactions[0]
            app_updated_at_round = latest_transaction["confirmed-round"]

            create_metadata = _parse_note(created_transaction.get("note"))
            update_metadata = _parse_note(latest_transaction.get("note"))

            if create_metadata and create_metadata.name:
                apps[create_metadata.name] = AppMetaData(
                    app_id=app_id,
                    app_address=get_application_address(app_id),
                    created_metadata=create_metadata,
                    created_round=app_created_at_round,
                    **(update_metadata or create_metadata).__dict__,
                    updated_round=app_updated_at_round,
                    deleted=app_deleted,
                )

        token = response.get("next-token")
        if not token:
            break

    return AppLookup(creator_address, apps)


def _state_schema(schema: dict[str, int]) -> StateSchema:
    return StateSchema(schema.get("num-uint", 0), schema.get("num-byte-slice", 0))  # type: ignore[no-untyped-call]


def _describe_schema_breaks(prefix: str, from_schema: StateSchema, to_schema: StateSchema) -> Iterable[str]:
    if to_schema.num_uints > from_schema.num_uints:
        yield f"{prefix} uints increased from {from_schema.num_uints} to {to_schema.num_uints}"
    if to_schema.num_byte_slices > from_schema.num_byte_slices:
        yield f"{prefix} byte slices increased from {from_schema.num_byte_slices} to {to_schema.num_byte_slices}"


@dataclasses.dataclass(kw_only=True)
class AppChanges:
    app_updated: bool
    schema_breaking_change: bool
    schema_change_description: str | None


def check_for_app_changes(
    algod_client: "AlgodClient",
    *,
    new_approval: bytes,
    new_clear: bytes,
    new_global_schema: StateSchema,
    new_local_schema: StateSchema,
    app_id: int,
) -> AppChanges:
    application_info = algod_client.application_info(app_id)
    assert isinstance(application_info, dict)
    application_create_params = application_info["params"]

    current_approval = base64.b64decode(application_create_params["approval-program"])
    current_clear = base64.b64decode(application_create_params["clear-state-program"])
    current_global_schema = _state_schema(application_create_params["global-state-schema"])
    current_local_schema = _state_schema(application_create_params["local-state-schema"])

    app_updated = current_approval != new_approval or current_clear != new_clear

    schema_changes: list[str] = []
    schema_changes.extend(_describe_schema_breaks("Global", current_global_schema, new_global_schema))
    schema_changes.extend(_describe_schema_breaks("Local", current_local_schema, new_local_schema))

    return AppChanges(
        app_updated=app_updated,
        schema_breaking_change=bool(schema_changes),
        schema_change_description=", ".join(schema_changes),
    )


def _is_valid_token_character(char: str) -> bool:
    return char.isalnum() or char == "_"


def _replace_template_variable(program_lines: list[str], template_variable: str, value: str) -> tuple[list[str], int]:
    result: list[str] = []
    match_count = 0
    token = f"TMPL_{template_variable}"
    token_idx_offset = len(value) - len(token)
    for line in program_lines:
        comment_idx = _find_unquoted_string(line, "//")
        if comment_idx is None:
            comment_idx = len(line)
        code = line[:comment_idx]
        comment = line[comment_idx:]
        trailing_idx = 0
        while True:
            token_idx = _find_template_token(code, token, trailing_idx)
            if token_idx is None:
                break

            trailing_idx = token_idx + len(token)
            prefix = code[:token_idx]
            suffix = code[trailing_idx:]
            code = f"{prefix}{value}{suffix}"
            match_count += 1
            trailing_idx += token_idx_offset
        result.append(code + comment)
    return result, match_count


def add_deploy_template_variables(
    template_values: TemplateValueDict, allow_update: bool | None, allow_delete: bool | None
) -> None:
    if allow_update is not None:
        template_values[_UPDATABLE] = int(allow_update)
    if allow_delete is not None:
        template_values[_DELETABLE] = int(allow_delete)


def _find_unquoted_string(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    """Find the first string within a line of TEAL. Only matches outside of quotes are returned.
    Returns None if not found"""

    if end < 0:
        end = len(line)
    idx = start
    in_quotes = False
    while idx < end:
        current_char = line[idx]
        match current_char:
            case "\\":
                if in_quotes:  # skip next character
                    idx += 1
            case '"':
                in_quotes = not in_quotes
            case _:
                # only match if not in quotes and string matches
                if not in_quotes and line.startswith(token, idx):
                    return idx
        idx += 1
    return None


def _find_template_token(line: str, token: str, start: int = 0, end: int = -1) -> int | None:
    """Find the first template token within a line of TEAL. Only matches outside of quotes are returned.
    Only full token matches are returned, i.e. TMPL_STR will not match against TMPL_STRING
    Returns None if not found"""
    if end < 0:
        end = len(line)

    idx = start
    while idx < end:
        token_idx = _find_unquoted_string(line, token, idx, end)
        if token_idx is None:
            break
        trailing_idx = token_idx + len(token)
        if (token_idx == 0 or not _is_valid_token_character(line[token_idx - 1])) and (  # word boundary at start
            trailing_idx >= len(line) or not _is_valid_token_character(line[trailing_idx])  # word boundary at end
        ):
            return token_idx
        idx = trailing_idx
    return None


def _strip_comment(line: str) -> str:
    comment_idx = _find_unquoted_string(line, "//")
    if comment_idx is None:
        return line
    return line[:comment_idx].rstrip()


def strip_comments(program: str) -> str:
    return "\n".join(_strip_comment(line) for line in program.splitlines())


def _has_token(program_without_comments: str, token: str) -> bool:
    for line in program_without_comments.splitlines():
        token_idx = _find_template_token(line, token)
        if token_idx is not None:
            return True
    return False


def _find_tokens(stripped_approval_program: str) -> list[str]:
    return _TOKEN_PATTERN.findall(stripped_approval_program)


def check_template_variables(approval_program: str, template_values: TemplateValueDict) -> None:
    approval_program = strip_comments(approval_program)
    if _has_token(approval_program, UPDATABLE_TEMPLATE_NAME) and _UPDATABLE not in template_values:
        raise DeploymentFailedError(
            "allow_update must be specified if deploy time configuration of update is being used"
        )
    if _has_token(approval_program, DELETABLE_TEMPLATE_NAME) and _DELETABLE not in template_values:
        raise DeploymentFailedError(
            "allow_delete must be specified if deploy time configuration of delete is being used"
        )
    all_tokens = _find_tokens(approval_program)
    missing_values = [token for token in all_tokens if token[len("TMPL_") :] not in template_values]
    if missing_values:
        raise DeploymentFailedError(f"The following template values were not provided: {', '.join(missing_values)}")

    for template_variable_name in template_values:
        tmpl_variable = f"TMPL_{template_variable_name}"
        if not _has_token(approval_program, tmpl_variable):
            if template_variable_name == _UPDATABLE:
                raise DeploymentFailedError(
                    "allow_update must only be specified if deploy time configuration of update is being used"
                )
            if template_variable_name == _DELETABLE:
                raise DeploymentFailedError(
                    "allow_delete must only be specified if deploy time configuration of delete is being used"
                )
            logger.warning(f"{tmpl_variable} not found in approval program, but variable was provided")


def replace_template_variables(program: str, template_values: TemplateValueMapping) -> str:
    """Replaces `TMPL_*` variables in `program` with `template_values`

    ```{note}
    `template_values` keys should *NOT* be prefixed with `TMPL_`
    ```
    """
    program_lines = program.splitlines()
    for template_variable_name, template_value in template_values.items():
        match template_value:
            case int():
                value = str(template_value)
            case str():
                value = "0x" + template_value.encode("utf-8").hex()
            case bytes():
                value = "0x" + template_value.hex()
            case _:
                raise DeploymentFailedError(
                    f"Unexpected template value type {template_variable_name}: {template_value.__class__}"
                )

        program_lines, matches = _replace_template_variable(program_lines, template_variable_name, value)

    return "\n".join(program_lines)


def has_template_vars(app_spec: ApplicationSpecification) -> bool:
    return "TMPL_" in strip_comments(app_spec.approval_program) or "TMPL_" in strip_comments(app_spec.clear_program)


def get_deploy_control(
    app_spec: ApplicationSpecification, template_var: str, on_complete: transaction.OnComplete
) -> bool | None:
    if template_var not in strip_comments(app_spec.approval_program):
        return None
    return get_call_config(app_spec.bare_call_config, on_complete) != CallConfig.NEVER or any(
        h for h in app_spec.hints.values() if get_call_config(h.call_config, on_complete) != CallConfig.NEVER
    )


def get_call_config(method_config: MethodConfigDict, on_complete: transaction.OnComplete) -> CallConfig:
    def get(key: OnCompleteActionName) -> CallConfig:
        return method_config.get(key, CallConfig.NEVER)

    match on_complete:
        case transaction.OnComplete.NoOpOC:
            return get("no_op")
        case transaction.OnComplete.UpdateApplicationOC:
            return get("update_application")
        case transaction.OnComplete.DeleteApplicationOC:
            return get("delete_application")
        case transaction.OnComplete.OptInOC:
            return get("opt_in")
        case transaction.OnComplete.CloseOutOC:
            return get("close_out")
        case transaction.OnComplete.ClearStateOC:
            return get("clear_state")


class OnUpdate(Enum):
    """Action to take if an Application has been updated"""

    Fail = 0
    """Fail the deployment"""
    UpdateApp = 1
    """Update the Application with the new approval and clear programs"""
    ReplaceApp = 2
    """Create a new Application and delete the old Application in a single transaction"""
    AppendApp = 3
    """Create a new application"""


class OnSchemaBreak(Enum):
    """Action to take if an Application's schema has breaking changes"""

    Fail = 0
    """Fail the deployment"""
    ReplaceApp = 2
    """Create a new Application and delete the old Application in a single transaction"""
    AppendApp = 3
    """Create a new Application"""


class OperationPerformed(Enum):
    """Describes the actions taken during deployment"""

    Nothing = 0
    """An existing Application was found"""
    Create = 1
    """No existing Application was found, created a new Application"""
    Update = 2
    """An existing Application was found, but was out of date, updated to latest version"""
    Replace = 3
    """An existing Application was found, but was out of date, created a new Application and deleted the original"""


@dataclasses.dataclass(kw_only=True)
class DeployResponse:
    """Describes the action taken during deployment, related transactions and the {py:class}`AppMetaData`"""

    app: AppMetaData
    create_response: TransactionResponse | None = None
    delete_response: TransactionResponse | None = None
    update_response: TransactionResponse | None = None
    action_taken: OperationPerformed = OperationPerformed.Nothing


@dataclasses.dataclass(kw_only=True)
class DeployCallArgs:
    """Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    suggested_params: transaction.SuggestedParams | None = None
    lease: bytes | str | None = None
    accounts: list[str] | None = None
    foreign_apps: list[int] | None = None
    foreign_assets: list[int] | None = None
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None
    rekey_to: str | None = None


@dataclasses.dataclass(kw_only=True)
class ABICall:
    method: ABIMethod | bool | None = None
    args: ABIArgsDict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(kw_only=True)
class DeployCreateCallArgs(DeployCallArgs):
    """Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    extra_pages: int | None = None
    on_complete: transaction.OnComplete | None = None


@dataclasses.dataclass(kw_only=True)
class ABICallArgs(DeployCallArgs, ABICall):
    """ABI Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""


@dataclasses.dataclass(kw_only=True)
class ABICreateCallArgs(DeployCreateCallArgs, ABICall):
    """ABI Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""


class DeployCallArgsDict(TypedDict, total=False):
    """Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    suggested_params: transaction.SuggestedParams
    lease: bytes | str
    accounts: list[str]
    foreign_apps: list[int]
    foreign_assets: list[int]
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]]
    rekey_to: str


class ABICallArgsDict(DeployCallArgsDict, TypedDict, total=False):
    """ABI Parameters used to update or delete an application when calling
    {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    method: ABIMethod | bool
    args: ABIArgsDict


class DeployCreateCallArgsDict(DeployCallArgsDict, TypedDict, total=False):
    """Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    extra_pages: int | None
    on_complete: transaction.OnComplete


class ABICreateCallArgsDict(DeployCreateCallArgsDict, TypedDict, total=False):
    """ABI Parameters used to create an application when calling {py:meth}`~algokit_utils.ApplicationClient.deploy`"""

    method: ABIMethod | bool
    args: ABIArgsDict


@dataclasses.dataclass(kw_only=True)
class Deployer:
    app_client: "ApplicationClient"
    creator: str
    signer: TransactionSigner
    sender: str
    existing_app_metadata_or_reference: AppReference | AppMetaData
    new_app_metadata: AppDeployMetaData
    on_update: OnUpdate
    on_schema_break: OnSchemaBreak
    create_args: ABICreateCallArgs | ABICreateCallArgsDict | DeployCreateCallArgs | None
    update_args: ABICallArgs | ABICallArgsDict | DeployCallArgs | None
    delete_args: ABICallArgs | ABICallArgsDict | DeployCallArgs | None

    def deploy(self) -> DeployResponse:
        """Ensures app associated with app client's creator is present and up to date"""
        assert self.app_client.approval
        assert self.app_client.clear

        if self.existing_app_metadata_or_reference.app_id == 0:
            logger.info(f"{self.new_app_metadata.name} not found in {self.creator} account, deploying app.")
            return self._create_app()

        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)
        logger.debug(
            f"{self.existing_app_metadata_or_reference.name} found in {self.creator} account, "
            f"with app id {self.existing_app_metadata_or_reference.app_id}, "
            f"version={self.existing_app_metadata_or_reference.version}."
        )

        app_changes = check_for_app_changes(
            self.app_client.algod_client,
            new_approval=self.app_client.approval.raw_binary,
            new_clear=self.app_client.clear.raw_binary,
            new_global_schema=self.app_client.app_spec.global_state_schema,
            new_local_schema=self.app_client.app_spec.local_state_schema,
            app_id=self.existing_app_metadata_or_reference.app_id,
        )

        if app_changes.schema_breaking_change:
            logger.warning(f"Detected a breaking app schema change: {app_changes.schema_change_description}")
            return self._deploy_breaking_change()

        if app_changes.app_updated:
            logger.info(f"Detected a TEAL update in app id {self.existing_app_metadata_or_reference.app_id}")
            return self._deploy_update()

        logger.info("No detected changes in app, nothing to do.")
        return DeployResponse(app=self.existing_app_metadata_or_reference)

    def _deploy_breaking_change(self) -> DeployResponse:
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)
        if self.on_schema_break == OnSchemaBreak.Fail:
            raise DeploymentFailedError(
                "Schema break detected and on_schema_break=OnSchemaBreak.Fail, stopping deployment. "
                "If you want to try deleting and recreating the app then "
                "re-run with on_schema_break=OnSchemaBreak.ReplaceApp"
            )
        if self.on_schema_break == OnSchemaBreak.AppendApp:
            logger.info("Schema break detected and on_schema_break=AppendApp, will attempt to create new app")
            return self._create_app()

        if self.existing_app_metadata_or_reference.deletable:
            logger.info(
                "App is deletable and on_schema_break=ReplaceApp, will attempt to create new app and delete old app"
            )
        elif self.existing_app_metadata_or_reference.deletable is False:
            logger.warning(
                "App is not deletable but on_schema_break=ReplaceApp, "
                "will attempt to delete app, delete will most likely fail"
            )
        else:
            logger.warning(
                "Cannot determine if App is deletable but on_schema_break=ReplaceApp, will attempt to delete app"
            )
        return self._create_and_delete_app()

    def _deploy_update(self) -> DeployResponse:
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)
        if self.on_update == OnUpdate.Fail:
            raise DeploymentFailedError(
                "Update detected and on_update=Fail, stopping deployment. "
                "If you want to try updating the app then re-run with on_update=UpdateApp"
            )
        if self.on_update == OnUpdate.AppendApp:
            logger.info("Update detected and on_update=AppendApp, will attempt to create new app")
            return self._create_app()
        elif self.existing_app_metadata_or_reference.updatable and self.on_update == OnUpdate.UpdateApp:
            logger.info("App is updatable and on_update=UpdateApp, will update app")
            return self._update_app()
        elif self.existing_app_metadata_or_reference.updatable and self.on_update == OnUpdate.ReplaceApp:
            logger.warning(
                "App is updatable but on_update=ReplaceApp, will attempt to create new app and delete old app"
            )
            return self._create_and_delete_app()
        elif self.on_update == OnUpdate.ReplaceApp:
            if self.existing_app_metadata_or_reference.updatable is False:
                logger.warning(
                    "App is not updatable and on_update=ReplaceApp, "
                    "will attempt to create new app and delete old app"
                )
            else:
                logger.warning(
                    "Cannot determine if App is updatable and on_update=ReplaceApp, "
                    "will attempt to create new app and delete old app"
                )
            return self._create_and_delete_app()
        else:
            if self.existing_app_metadata_or_reference.updatable is False:
                logger.warning(
                    "App is not updatable but on_update=UpdateApp, "
                    "will attempt to update app, update will most likely fail"
                )
            else:
                logger.warning(
                    "Cannot determine if App is updatable and on_update=UpdateApp, will attempt to update app"
                )
            return self._update_app()

    def _create_app(self) -> DeployResponse:
        assert self.app_client.existing_deployments

        method, abi_args, parameters = _convert_deploy_args(
            self.create_args, self.new_app_metadata, self.signer, self.sender
        )
        create_response = self.app_client.create(
            method,
            parameters,
            **abi_args,
        )
        logger.info(
            f"{self.new_app_metadata.name} ({self.new_app_metadata.version}) deployed successfully, "
            f"with app id {self.app_client.app_id}."
        )
        assert create_response.confirmed_round is not None
        app_metadata = _create_metadata(self.new_app_metadata, self.app_client.app_id, create_response.confirmed_round)
        self.app_client.existing_deployments.apps[self.new_app_metadata.name] = app_metadata
        return DeployResponse(app=app_metadata, create_response=create_response, action_taken=OperationPerformed.Create)

    def _create_and_delete_app(self) -> DeployResponse:
        assert self.app_client.existing_deployments
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)

        logger.info(
            f"Replacing {self.existing_app_metadata_or_reference.name} "
            f"({self.existing_app_metadata_or_reference.version}) with "
            f"{self.new_app_metadata.name} ({self.new_app_metadata.version}) in {self.creator} account."
        )
        atc = AtomicTransactionComposer()
        create_method, create_abi_args, create_parameters = _convert_deploy_args(
            self.create_args, self.new_app_metadata, self.signer, self.sender
        )
        self.app_client.compose_create(
            atc,
            create_method,
            create_parameters,
            **create_abi_args,
        )
        create_txn_index = len(atc.txn_list) - 1
        delete_method, delete_abi_args, delete_parameters = _convert_deploy_args(
            self.delete_args, self.new_app_metadata, self.signer, self.sender
        )
        self.app_client.compose_delete(
            atc,
            delete_method,
            delete_parameters,
            **delete_abi_args,
        )
        delete_txn_index = len(atc.txn_list) - 1
        create_delete_response = self.app_client.execute_atc(atc)
        create_response = TransactionResponse.from_atr(create_delete_response, create_txn_index)
        delete_response = TransactionResponse.from_atr(create_delete_response, delete_txn_index)
        self.app_client.app_id = get_app_id_from_tx_id(self.app_client.algod_client, create_response.tx_id)
        logger.info(
            f"{self.new_app_metadata.name} ({self.new_app_metadata.version}) deployed successfully, "
            f"with app id {self.app_client.app_id}."
        )
        logger.info(
            f"{self.existing_app_metadata_or_reference.name} "
            f"({self.existing_app_metadata_or_reference.version}) with app id "
            f"{self.existing_app_metadata_or_reference.app_id}, deleted successfully."
        )

        app_metadata = _create_metadata(
            self.new_app_metadata, self.app_client.app_id, create_delete_response.confirmed_round
        )
        self.app_client.existing_deployments.apps[self.new_app_metadata.name] = app_metadata

        return DeployResponse(
            app=app_metadata,
            create_response=create_response,
            delete_response=delete_response,
            action_taken=OperationPerformed.Replace,
        )

    def _update_app(self) -> DeployResponse:
        assert self.app_client.existing_deployments
        assert isinstance(self.existing_app_metadata_or_reference, AppMetaData)

        logger.info(
            f"Updating {self.existing_app_metadata_or_reference.name} to {self.new_app_metadata.version} in "
            f"{self.creator} account, with app id {self.existing_app_metadata_or_reference.app_id}"
        )
        method, abi_args, parameters = _convert_deploy_args(
            self.update_args, self.new_app_metadata, self.signer, self.sender
        )
        update_response = self.app_client.update(
            method,
            parameters,
            **abi_args,
        )
        app_metadata = _create_metadata(
            self.new_app_metadata,
            self.app_client.app_id,
            self.existing_app_metadata_or_reference.created_round,
            updated_round=update_response.confirmed_round,
            original_metadata=self.existing_app_metadata_or_reference.created_metadata,
        )
        self.app_client.existing_deployments.apps[self.new_app_metadata.name] = app_metadata
        return DeployResponse(app=app_metadata, update_response=update_response, action_taken=OperationPerformed.Update)


def _create_metadata(
    app_spec_note: AppDeployMetaData,
    app_id: int,
    created_round: int,
    updated_round: int | None = None,
    original_metadata: AppDeployMetaData | None = None,
) -> AppMetaData:
    return AppMetaData(
        app_id=app_id,
        app_address=get_application_address(app_id),
        created_metadata=original_metadata or app_spec_note,
        created_round=created_round,
        updated_round=updated_round or created_round,
        name=app_spec_note.name,
        version=app_spec_note.version,
        deletable=app_spec_note.deletable,
        updatable=app_spec_note.updatable,
        deleted=False,
    )


def _convert_deploy_args(
    _args: DeployCallArgs | DeployCallArgsDict | None,
    note: AppDeployMetaData,
    signer: TransactionSigner | None,
    sender: str | None,
) -> tuple[ABIMethod | bool | None, ABIArgsDict, CreateCallParameters]:
    args = _args.__dict__ if isinstance(_args, DeployCallArgs) else (_args or {})

    # return most derived type, unused parameters are ignored
    parameters = CreateCallParameters(
        note=note.encode(),
        signer=signer,
        sender=sender,
        suggested_params=args.get("suggested_params"),
        lease=args.get("lease"),
        accounts=args.get("accounts"),
        foreign_assets=args.get("foreign_assets"),
        foreign_apps=args.get("foreign_apps"),
        boxes=args.get("boxes"),
        rekey_to=args.get("rekey_to"),
        extra_pages=args.get("extra_pages"),
        on_complete=args.get("on_complete"),
    )

    return args.get("method"), args.get("args") or {}, parameters


def get_app_id_from_tx_id(algod_client: "AlgodClient", tx_id: str) -> int:
    """Finds the app_id for provided transaction id"""
    result = algod_client.pending_transaction_info(tx_id)
    assert isinstance(result, dict)
    app_id = result["application-index"]
    assert isinstance(app_id, int)
    return app_id
