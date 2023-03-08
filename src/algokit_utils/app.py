import base64
import dataclasses
import json
import logging

from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.logic import get_application_address
from algosdk.transaction import StateSchema, SuggestedParams
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algokit_utils.application_client import ApplicationClient
from algokit_utils.application_specification import ApplicationSpecification
from algokit_utils.models import Account

logger = logging.getLogger(__name__)

DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT = 1000


class DeploymentFailedError(Exception):
    pass


@dataclasses.dataclass
class AppNote:
    name: str
    version: str
    deletable: bool
    updatable: bool

    @staticmethod
    def from_json(value: str) -> "AppNote":
        return AppNote(**json.loads(value))


@dataclasses.dataclass
class App:
    id: int
    address: str
    created_at_round: int
    note: AppNote


def create_note(app_spec: ApplicationSpecification, version: str) -> AppNote:
    return AppNote(app_spec.contract.name, version, app_spec.deletable, app_spec.updatable)


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


def deploy_app(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: ApplicationSpecification,
    creator_account: Account,
    version: str,
    *,
    # TODO: enums
    delete_app_on_schema_break: bool = False,
    delete_app_on_update: bool = False,
    # allow_update: bool -> TMPL
    # allow_delete: bool -> TMPL
    # on_update: NO, Update, Delete
    # on_schema_break: No, Delete
    # TODO: TMPL values
) -> App:
    # TODO: return ApplicationClient

    # TODO: deploy time control
    # TMPL _deletable
    # TMPL _updatable
    # add blueprint for these
    # fall back to reading app spec

    # TODO: what about template substitution?

    # TODO: allow resolve app id via environment variable
    apps = get_creator_apps(indexer_client, creator_account)
    name = app_spec.contract.name  # TODO: contract name is app name?

    app = apps.get(name)
    if app is None:
        logger.info(f"{name} not found in {creator_account.address} account, deploying app.")
        app_client = ApplicationClient(
            algod_client, app_spec, signer=AccountTransactionSigner(creator_account.private_key)
        )

        app_note = create_note(app_spec, version)
        create_result = app_client.create(note=encode_note(app_note))
        logger.info(f"{name} ({version}) deployed successfully, with app id {create_result.app_id}.")
        return App(create_result.app_id, create_result.app_address, create_result.confirmed_round, app_note)

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
            # TODO: warn depending on environment?
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
            # TODO: include environment check
            raise DeploymentFailedError(
                "Stopping deployment. If you want to delete and recreate the app "
                "then re-run with delete_app_on_update=True"
            )

    if schema_breaking_change or (app_updated and delete_app_on_update):
        logger.info(f"Deploying {name} ({version}) in {creator_account.address} account.")
        app_client = ApplicationClient(
            algod_client, app_spec, signer=AccountTransactionSigner(creator_account.private_key)
        )

        app_note = create_note(app_spec, version)
        create_result = app_client.create(note=encode_note(app_note))
        logger.info(f"{name} ({version}) deployed successfully, with app id {create_result.app_id}.")

        # delete the old app
        logger.info(f"Deleting {name} ({app.note.version}) in {creator_account.address} account, with app id {app.id}")
        old_app_client = ApplicationClient(
            algod_client, app_spec, app_id=app.id, signer=AccountTransactionSigner(creator_account.private_key)
        )
        old_app_client.delete()
        return App(create_result.app_id, create_result.app_address, create_result.confirmed_round, app_note)
    elif app_updated:
        logger.info(f"Updating {name} to {version} in {creator_account.address} account, with app id {app.id}")
        app_client = ApplicationClient(
            algod_client, app_spec, app_id=app.id, signer=AccountTransactionSigner(creator_account.private_key)
        )
        app_note = create_note(app_spec, version)
        update_result = app_client.update(note=encode_note(app_note))
        return App(update_result.app_id, update_result.app_address, update_result.confirmed_round, app_note)
    return app
