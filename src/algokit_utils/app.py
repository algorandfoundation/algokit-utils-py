import base64
import dataclasses
import json
import logging
import re

from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.logic import get_application_address
from algosdk.transaction import StateSchema, SuggestedParams
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from pyteal import CallConfig

from algokit_utils.application_client import ApplicationClient
from algokit_utils.application_specification import ApplicationSpecification
from algokit_utils.models import Account

logger = logging.getLogger(__name__)

DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT = 1000
UPDATABLE_TEMPLATE_NAME = "TMPL_UPDATABLE"
DELETABLE_TEMPLATE_NAME = "TMPL_DELETABLE"


class DeploymentFailedError(Exception):
    pass


@dataclasses.dataclass
class AppNote:
    name: str
    version: str
    deletable: bool = dataclasses.field(kw_only=True)
    updatable: bool = dataclasses.field(kw_only=True)

    @staticmethod
    def from_json(value: str) -> "AppNote":
        return AppNote(**json.loads(value))


@dataclasses.dataclass
class App:
    id: int
    address: str
    created_at_round: int
    note: AppNote


def encode_note(note: AppNote) -> bytes:
    json_str = json.dumps(note.__dict__)
    return json_str.encode("utf-8")


def get_creator_apps(indexer: IndexerClient, creator_account: Account | str) -> dict[str, App]:
    apps: dict[str, App] = {}

    creator_address = creator_account if isinstance(creator_account, str) else creator_account.address
    token = None
    # TODO: abstract pagination logic?
    while True:
        response = indexer.lookup_account_application_by_creator(
            creator_address, limit=DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT, next_page=token
        )  # type: ignore[no-untyped-call]
        if "message" in response:  # an error occurred
            raise Exception(f"Error querying applications for {creator_address}: {response}")
        for app in response["applications"]:
            app_id = app["id"]
            app_created_at_round = app["created-at-round"]
            transactions_response = indexer.search_transactions(
                min_round=app_created_at_round, max_round=app_created_at_round, txn_type="appl", application_id=app_id
            )  # type: ignore[no-untyped-call]
            creation_transaction = next(
                t
                for t in transactions_response["transactions"]
                if t["application-transaction"]["application-id"] == 0 and t["sender"] == creator_address
            )
            note_json = creation_transaction.get("note")
            if not note_json:
                continue
            note_json = base64.b64decode(note_json).decode("utf-8")
            try:
                app_note = AppNote.from_json(note_json)
            except json.decoder.JSONDecodeError:
                continue
            apps[app_note.name] = App(app_id, get_application_address(app_id), app_created_at_round, app_note)

        token = response.get("next-token")
        if not token:
            break

    return apps


# TODO: put these somewhere more useful
def _state_schema(schema: dict[str, int]) -> StateSchema:
    return StateSchema(schema.get("num-uint", 0), schema.get("num-byte-slice", 0))  # type: ignore[no-untyped-call]


def _schema_is_less(a: StateSchema, b: StateSchema) -> bool:
    return bool(a.num_uints < b.num_uints or a.num_byte_slices < b.num_byte_slices)


def _schema_str(global_schema: StateSchema, local_schema: StateSchema) -> str:
    return (
        f"Global: uints={global_schema.num_uints}, byte_slices={global_schema.num_byte_slices}, "
        f"Local: uints={local_schema.num_uints}, byte_slices={local_schema.num_byte_slices}"
    )


def get_application_client(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    creator_account: Account | str,
    app_spec: ApplicationSpecification,
    *,
    signer: TransactionSigner | None = None,
    sender: str | None = None,
    suggested_params: SuggestedParams | None = None,
) -> ApplicationClient | None:
    creator_address = creator_account if isinstance(creator_account, str) else creator_account.address
    apps = get_creator_apps(indexer_client, creator_address)

    app_name = app_spec.contract.name
    app = apps.get(app_name)
    if not app:
        logger.info(f"Could not find app {app_name} in account {creator_address}.")
        return None

    logger.info(f"{app_name} ({app.note.version}) found in {creator_address} account with app id {app.id}.")

    return ApplicationClient(
        algod_client, app_spec, app_id=app.id, signer=signer, sender=sender, suggested_params=suggested_params
    )


def _replace_template_variable(program_lines: list[str], template_variable: str, value: str) -> tuple[list[str], int]:
    result: list[str] = []
    match_count = 0
    pattern = re.compile(rf"(\b){template_variable}(\b|$)")

    def replacement(m: re.Match) -> str:
        return f"{m.group(1)}{value}{m.group(2)}"

    for line in program_lines:
        code_comment = line.split("//", maxsplit=1)
        code = code_comment[0]
        new_line, matches = re.subn(pattern, replacement, code)
        match_count += matches
        if len(code_comment) > 1:
            new_line = f"{new_line}//{code_comment[1]}"
        result.append(new_line)
    return result, match_count


def _merge_template_variables(
    template_values: dict[str, int | str] | None, allow_update: bool | None, allow_delete: bool | None
) -> dict[str, int | str]:
    merged_template_values: dict[str, int | str] = {f"TMPL_{k}": v for k, v in (template_values or {}).items()}
    if allow_update is not None:
        merged_template_values[UPDATABLE_TEMPLATE_NAME] = int(allow_update)
    if allow_delete is not None:
        merged_template_values[DELETABLE_TEMPLATE_NAME] = int(allow_delete)
    return merged_template_values


def _check_template_variables(approval_program: str, template_values: dict[str, int | str]) -> None:
    if UPDATABLE_TEMPLATE_NAME in approval_program and UPDATABLE_TEMPLATE_NAME not in template_values:
        raise DeploymentFailedError(
            "allow_update must be specified if deploy time configuration of update is being used"
        )
    if DELETABLE_TEMPLATE_NAME in approval_program and DELETABLE_TEMPLATE_NAME not in template_values:
        raise DeploymentFailedError(
            "allow_delete must be specified if deploy time configuration of delete is being used"
        )

    for template_variable_name in template_values:
        if template_variable_name not in approval_program:
            if template_variable_name == UPDATABLE_TEMPLATE_NAME:
                raise DeploymentFailedError(
                    "allow_update must only be specified if deploy time configuration of update is being used"
                )
            elif template_variable_name == DELETABLE_TEMPLATE_NAME:
                raise DeploymentFailedError(
                    "allow_delete must only be specified if deploy time configuration of delete is being used"
                )
            else:
                logger.warning(f"{template_variable_name} not found in approval program, but variable was provided")


def replace_template_variables(program: str, template_values: dict[str, int | str]) -> str:
    program_lines = program.splitlines()
    for template_variable_name, template_value in template_values.items():
        value = str(template_value) if isinstance(template_value, int) else "0x" + template_value.encode("utf-8").hex()
        program_lines, matches = _replace_template_variable(program_lines, template_variable_name, value)

    result = "\n".join(program_lines)
    return result


def deploy_app(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: ApplicationSpecification,
    creator_account: Account,
    version: str,
    *,
    # TODO: enums
    # on_update: NO, Update, Delete
    # on_schema_break: No, Delete
    delete_app_on_schema_break: bool = False,
    delete_app_on_update: bool = False,
    allow_update: bool | None = None,
    allow_delete: bool | None = None,
    template_values: dict[str, int | str] | None = None,
) -> App:
    # TODO: return ApplicationClient

    approval_template_values = _merge_template_variables(template_values, allow_update, allow_delete)
    _check_template_variables(app_spec.approval_program, approval_template_values)

    app_spec.approval_program = replace_template_variables(app_spec.approval_program, approval_template_values)
    app_spec.clear_program = replace_template_variables(app_spec.clear_program, template_values or {})
    # add blueprint for these
    updatable = (
        allow_update
        if allow_update is not None
        else (
            app_spec.bare_call_config.update_application != CallConfig.NEVER
            or any(h for h in app_spec.hints.values() if h.call_config.update_application != CallConfig.NEVER)
        )
    )

    deletable = (
        allow_delete
        if allow_delete is not None
        else (
            app_spec.bare_call_config.delete_application != CallConfig.NEVER
            or any(h for h in app_spec.hints.values() if h.call_config.delete_application != CallConfig.NEVER)
        )
    )

    name = app_spec.contract.name
    app_spec_note = AppNote(name, version, updatable=updatable, deletable=deletable)

    # TODO: allow resolve app id via environment variable
    apps = get_creator_apps(indexer_client, creator_account)
    app = apps.get(name)

    if app is None:
        logger.info(f"{name} not found in {creator_account.address} account, deploying app.")
        app_client = ApplicationClient(
            algod_client, app_spec, signer=AccountTransactionSigner(creator_account.private_key)
        )

        create_result = app_client.create(note=encode_note(app_spec_note))
        logger.info(f"{name} ({version}) deployed successfully, with app id {create_result.app_id}.")
        return App(create_result.app_id, create_result.app_address, create_result.confirmed_round, app_spec_note)

    logger.debug(
        f"{name} found in {creator_account.address} account, with app id {app.id}, version={app.note.version}."
    )
    application_info = indexer_client.applications(app.id)  # type: ignore[no-untyped-call]
    application_create_params = application_info["application"]["params"]

    current_approval = application_create_params["approval-program"]
    current_clear = application_create_params["clear-state-program"]
    current_global_schema = _state_schema(application_create_params["global-state-schema"])
    current_local_schema = _state_schema(application_create_params["local-state-schema"])

    required_global_schema = app_spec.global_state_schema
    required_local_schema = app_spec.local_state_schema
    new_approval = app_spec.approval_program
    new_clear = app_spec.clear_program

    app_updated = current_approval != new_approval or current_clear != new_clear

    schema_breaking_change = _schema_is_less(current_global_schema, required_global_schema) or _schema_is_less(
        current_local_schema, required_local_schema
    )
    if schema_breaking_change:
        logger.warning(
            f"Detected a breaking app schema change from "
            f"{_schema_str(current_global_schema, current_local_schema)} to "
            f"{_schema_str(required_global_schema, required_local_schema)}."
        )

        if app.note.deletable:
            logger.warning("App is deletable. Creating new app and then deleting old one")
        elif delete_app_on_schema_break:
            logger.warning("Received delete_app_on_schema_break=True. Creating new app and then deleting old one")
        else:
            raise DeploymentFailedError(
                "Stopping deployment. If you want to delete and recreate the app "
                "then re-run with delete_app_on_schema_break=True"
            )

    elif app_updated:
        logger.info(f"Detected a TEAL update in app id {app.id}")

        if app.note.updatable:
            logger.info("App is updatable. Will perform update application transaction")
        elif delete_app_on_update:
            logger.warning("Received delete_app_on_update=True. Creating new app and then deleting old one")
        else:
            raise DeploymentFailedError(
                "Stopping deployment. If you want to delete and recreate the app "
                "then re-run with delete_app_on_update=True"
            )

    if schema_breaking_change or (app_updated and delete_app_on_update):
        logger.info(f"Deploying {name} ({version}) in {creator_account.address} account.")
        app_client = ApplicationClient(
            algod_client, app_spec, signer=AccountTransactionSigner(creator_account.private_key)
        )

        create_result = app_client.create(note=encode_note(app_spec_note))
        logger.info(f"{name} ({version}) deployed successfully, with app id {create_result.app_id}.")

        # delete the old app
        logger.info(f"Deleting {name} ({app.note.version}) in {creator_account.address} account, with app id {app.id}")
        old_app_client = ApplicationClient(
            algod_client, app_spec, app_id=app.id, signer=AccountTransactionSigner(creator_account.private_key)
        )
        old_app_client.delete()
        return App(create_result.app_id, create_result.app_address, create_result.confirmed_round, app_spec_note)
    elif app_updated:
        logger.info(f"Updating {name} to {version} in {creator_account.address} account, with app id {app.id}")
        app_client = ApplicationClient(
            algod_client, app_spec, app_id=app.id, signer=AccountTransactionSigner(creator_account.private_key)
        )
        update_result = app_client.update(note=encode_note(app_spec_note))
        return App(update_result.app_id, update_result.app_address, update_result.confirmed_round, app_spec_note)
    return app
