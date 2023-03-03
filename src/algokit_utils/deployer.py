import base64
import dataclasses
import json
import logging
import os
import re
from collections.abc import Callable
from typing import Any

import algosdk
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.kmd import KMDClient
from algosdk.transaction import PaymentTxn, StateSchema
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv

from algokit_utils.application_client import ApplicationClient
from algokit_utils.application_specification import ApplicationSpecification

# mypy: allow-untyped-calls,
# mypy: disable_error_code = attr-defined
# mypy: disable_error_code = name-defined

# TODO: organize these functions into modules

# TODO: should this library be doing this
load_dotenv()

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class AlgoClientConfig:
    server: str
    token: str | None = None


def _get_config_from_environment(environment_prefix: str) -> AlgoClientConfig:
    server = os.getenv(f"{environment_prefix}_SERVER")
    if server is None:
        raise Exception(f"Server environment variable not set: {environment_prefix}_SERVER")
    return AlgoClientConfig(server, os.getenv(f"{environment_prefix}_TOKEN"))


def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
    # TODO: alternate headers etc.
    config = config or _get_config_from_environment("ALGOD")
    return AlgodClient(config.token, config.server)


def get_indexer_client(config: AlgoClientConfig | None = None) -> IndexerClient:
    config = config or _get_config_from_environment("INDEXER")
    return IndexerClient(config.token, config.server)


@dataclasses.dataclass
class Account:
    private_key: str
    address: str


def get_account_from_mnemonic(mnemonic: str) -> Account:
    private_key = algosdk.mnemonic.to_private_key(mnemonic)
    address = algosdk.account.address_from_private_key(private_key)
    return Account(private_key, address)


def is_sandbox(client: AlgodClient) -> bool:
    params = client.suggested_params()
    return params.gen in ["devnet-v1", "sandnet-v1"]


def _replace_kmd_port(address: str, port: str) -> str:
    # TODO: parse this properly

    match = re.search(r"(:[0-9]+/?)$", address)
    if match:
        address = address[: -len(match.group(1))]
    return f"{address}:{port}"


def _get_kmd_client_from_algod_client(client: AlgodClient) -> KMDClient:
    # We can only use Kmd on the Sandbox otherwise it's not exposed so this makes some assumptions
    # (e.g. same token and server as algod and port 4002 by default)
    port = os.getenv("KMD_PORT", "4002")
    server = _replace_kmd_port(client.algod_address, port)
    return KMDClient(client.algod_token, server)


def get_or_create_kmd_wallet_account(
    client: AlgodClient, name: str, fund_with: int | None, kmd_client: KMDClient | None = None
) -> Account:
    kmd_client = kmd_client or _get_kmd_client_from_algod_client(client)
    fund_with = 1000 if fund_with is None else fund_with
    account = get_kmd_wallet_account(client, kmd_client, name)

    if account:
        account_info = client.account_info(account.address)
        if account_info["amount"] > 0:
            return account
        logger.debug(f"Found existing account in Sandbox with name '{name}'." f"But no funds in the account.")
    else:
        wallet_id = kmd_client.create_wallet(name, "")["id"]
        wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")
        kmd_client.generate_key(wallet_handle)

        account = get_kmd_wallet_account(client, kmd_client, name)
        assert account
        logger.debug(
            f"Couldn't find existing account in Sandbox with name '{name}'."
            f"So created account {account.address} with keys stored in KMD."
        )

    logger.debug(f"Funding account {account.address} with {fund_with} ALGOs")

    transfer(
        TransferParameters(
            from_account=get_dispenser_account(client),
            to_address=account.address,
            amount=algosdk.util.algos_to_microalgos(fund_with),
        ),
        client,
    )

    return account


def _is_default_account(account: dict[str, Any]) -> bool:
    return bool(account["status"] != "Offline" and account["amount"] > 1_000_000_000)


def get_sandbox_default_account(client: AlgodClient) -> Account:
    if not is_sandbox(client):
        raise Exception("Can't get a default account from non Sandbox network")

    account = get_kmd_wallet_account(
        client, _get_kmd_client_from_algod_client(client), "unencrypted-default-wallet", _is_default_account
    )
    assert account
    return account


def get_dispenser_account(client: AlgodClient) -> Account:
    if is_sandbox(client):
        return get_sandbox_default_account(client)
    return get_account(client, "DISPENSER")


@dataclasses.dataclass
class TransferParameters:
    from_account: Account
    to_address: str
    amount: int  # micro algos
    note: str | None = None
    skip_sending: bool = False
    skip_waiting: bool = False
    max_fee_in_algos: int | None = None  # TODO: micro algos?


def transfer(transfer_parameters: TransferParameters, client: AlgodClient) -> PaymentTxn:
    suggested_params = client.suggested_params()
    transaction = algosdk.transaction.PaymentTxn(
        sender=transfer_parameters.from_account.address,
        sp=suggested_params,
        receiver=transfer_parameters.to_address,
        amt=transfer_parameters.amount,
        close_remainder_to=None,
        note=transfer_parameters.note.encode("utf-8") if transfer_parameters.note else None,
        rekey_to=None,
    )

    if not transfer_parameters.skip_sending:
        return send_transaction(
            client,
            transaction,
            transfer_parameters.from_account,
            skip_waiting=transfer_parameters.skip_waiting,
            max_fee=transfer_parameters.max_fee_in_algos or 0.02,
        )

    return transaction


def send_transaction(
    client: AlgodClient,
    transaction: PaymentTxn,
    from_account: Account,  # TODO: logic signature support
    *,
    skip_waiting: bool,
    max_fee: float,
) -> PaymentTxn:
    # TODO: cap fee

    signed_transaction = transaction.sign(from_account.private_key)
    client.send_transaction(signed_transaction)

    logger.debug(f"Sent transaction id '{transaction.get_txid()}' {transaction.type} from {from_account.address}")

    if not skip_waiting:
        # TODO: wait for confirmation
        pass

    return transaction


def get_kmd_wallet_account(
    client: AlgodClient, kmd_client: KMDClient, name: str, predicate: Callable[[dict[str, Any]], bool] | None = None
) -> Account | None:
    wallets: list[dict] = kmd_client.list_wallets()

    wallet = next((w for w in wallets if w["name"] == name), None)
    if wallet is None:
        return None

    wallet_id = wallet["id"]
    wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")
    key_ids: list[str] = kmd_client.list_keys(wallet_handle)
    matched_account_key = None
    if predicate:
        for key in key_ids:
            account = client.account_info(key)
            if predicate(account):
                matched_account_key = key
    else:
        matched_account_key = next(key_ids.__iter__(), None)

    if not matched_account_key:
        return None

    private_account_key = kmd_client.export_key(wallet_handle, "", matched_account_key)
    return get_account_from_mnemonic(algosdk.mnemonic.from_private_key(private_account_key))


def get_account(
    client: AlgodClient, name: str, fund_with: int | None = None, kmd_client: KMDClient | None = None
) -> Account:
    mnemonic_key = f"{name.upper()}_MNEMONIC"
    mnemonic = os.getenv(mnemonic_key)
    if mnemonic:
        return get_account_from_mnemonic(mnemonic)

    if is_sandbox(client):
        account = get_or_create_kmd_wallet_account(client, name, fund_with, kmd_client)
        os.environ[mnemonic_key] = account.private_key
        return account

    raise Exception(f"Missing environment variable '{mnemonic_key}' when looking for account '{name}'")


@dataclasses.dataclass
class App:
    id: int
    address: str


DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT = 1000


def get_creator_apps(indexer: IndexerClient, creator_account: Account | str) -> dict[str, App]:
    apps: dict[str, App] = {}

    creator_address = creator_account if isinstance(creator_account, str) else creator_account.address
    token = None
    # TODO: abstract pagination logic?
    while True:
        response = indexer.lookup_account_application_by_creator(
            creator_address, limit=DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT, next_page=token
        )
        if "message" in response:  # an error occurred
            raise Exception(f"Error querying applications for {creator_address}: {response}")
        for app in response["applications"]:
            app_id = app["id"]
            app_created_at_round = app["created-at-round"]
            transactions_response = indexer.search_transactions(
                min_round=app_created_at_round, max_round=app_created_at_round, txn_type="appl", application_id=app_id
            )
            creation_transaction = next(
                t
                for t in transactions_response["transactions"]
                if t["application-transaction"]["application-id"] == 0 and t["sender"] == creator_address
            )
            note = creation_transaction.get("note")
            if not note:
                continue
            note = base64.b64decode(note).decode("utf-8")
            try:
                app_data = json.loads(note)
            except json.decoder.JSONDecodeError:
                continue
            app_name = app_data.get("name")
            apps[app_name] = App(app_id, algosdk.logic.get_application_address(app_id))

        token = response.get("next-token")
        if not token:
            break

    return apps


@dataclasses.dataclass
class AppNote:
    name: str
    version: str


def encode_note(note: AppNote) -> bytes:
    json_str = json.dumps(note.__dict__)
    return json_str.encode("utf-8")


# TODO: get app client from creator and app name


def deploy_app(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: ApplicationSpecification,
    creator_account: Account,
    version: str,
    *,
    delete_app_on_schema_break: bool = False,
    delete_app_on_update_if_exists: bool = False,
) -> App:
    # TODO: return ApplicationClient

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
        create_result = app_client.create(note=encode_note(AppNote(name, version)))
        logger.info(f"{name} deployed successfully, with app id {create_result.app_id}.")
        return App(create_result.app_id, create_result.app_address)

    logger.debug(f"{name} found in {creator_account.address} account, with app id {app.id}.")
    application_create_params = indexer_client.applications(app.id)["application"]["params"]

    # TODO: put these somewhere more useful
    def _state_schema(schema: dict[str, int]) -> StateSchema:
        return StateSchema(schema.get("num-uint", 0), schema.get("num-byte-slice", 0))

    def _schema_is_less(a: StateSchema, b: StateSchema) -> bool:
        return bool(a.num_uints < b.num_uints or a.num_byte_slices < b.num_byte_slices)

    def _schema_str(global_schema: StateSchema, local_schema: StateSchema) -> str:
        return (
            f"Global: uints={global_schema.num_uints}, byte_slices={global_schema.num_byte_slices}, "
            f"Local: uints={local_schema.num_uints}, byte_slices={local_schema.num_byte_slices}"
        )

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
            f"{_schema_str(current_global_schema, current_local_schema)} to"
            f"{_schema_str(required_global_schema, required_local_schema)}."
        )

        if not delete_app_on_schema_break:
            # TODO: include environment check
            raise Exception(
                "Stopping deployment. If you want to delete and recreate the app "
                "then re-run with delete_app_on_schema_break=True"
            )
        logger.warning("Received delete_app_on_schema_break=True. Creating new app and then deleting old one")

    if app_updated:
        logger.info(f"Detected a TEAL update in app {app.id}")

        if not delete_app_on_update_if_exists:
            # TODO: include environment check
            raise Exception(
                "Stopping deployment. If you want to delete and recreate the app "
                "then re-run with delete_app_on_update_if_exists=True"
            )

        logger.warning("Received delete_app_on_update_if_exists=True. Creating new app and then deleting old one")

    if schema_breaking_change or (app_updated and delete_app_on_update_if_exists):
        logger.info(f"Deploying new version of {name} in {creator_account.address} account.")
        app_client = ApplicationClient(
            algod_client, app_spec, app_id=app.id, signer=AccountTransactionSigner(creator_account.private_key)
        )

        create_result = app_client.create(note=encode_note(AppNote(name, version)))

        # delete the old app
        logger.info(f"Deleting old version of {name} in {creator_account.address} account, with app id {app.id}")
        old_app_client = ApplicationClient(
            algod_client, app_spec, app_id=app.id, signer=AccountTransactionSigner(creator_account.private_key)
        )
        old_app_client.delete()
        return App(create_result.app_id, create_result.app_address)
    elif app_updated:
        logger.info(f"Updating to new version of {name} in {creator_account.address} account, with app id {app.id}")
        app_client = ApplicationClient(
            algod_client, app_spec, app_id=app.id, signer=AccountTransactionSigner(creator_account.private_key)
        )
        app_client.update(note=encode_note(AppNote(name, version)))
    return app
