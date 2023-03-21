import base64
import dataclasses
import json
import logging
import re
import typing

from algosdk.logic import get_application_address
from algosdk.transaction import StateSchema

if typing.TYPE_CHECKING:
    from algosdk.v2client.indexer import IndexerClient

    from algokit_utils.models import Account

logger = logging.getLogger(__name__)

DEFAULT_INDEXER_MAX_API_RESOURCES_PER_ACCOUNT = 1000
_UPDATABLE = "UPDATABLE"
_DELETABLE = "DELETABLE"
UPDATABLE_TEMPLATE_NAME = f"TMPL_{_UPDATABLE}"
DELETABLE_TEMPLATE_NAME = f"TMPL_{_DELETABLE}"
TemplateValueDict = dict[str, int | str | bytes]

NOTE_PREFIX = "ALGOKIT_DEPLOYER:j"  # this prefix also makes the note ARC-2 compliant
# when base64 encoding bytes, 3 bytes are stored in every 4 characters
# assert the NOTE_PREFIX length is a multiple of 3, so we don't need to worry about the
# padding/changing characters at the end
assert len(NOTE_PREFIX) % 3 == 0


class DeploymentFailedError(Exception):
    pass


@dataclasses.dataclass
class AppReference:
    app_id: int
    app_address: str


@dataclasses.dataclass
class AppDeployMetaData:
    name: str
    version: str
    deletable: bool | None
    updatable: bool | None

    @staticmethod
    def from_json(value: str) -> "AppDeployMetaData":
        return AppDeployMetaData(**json.loads(value))

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
    created_round: int
    updated_round: int
    created_metadata: AppDeployMetaData
    deleted: bool


@dataclasses.dataclass
class AppLookup:
    creator: str
    apps: dict[str, AppMetaData] = dataclasses.field(default_factory=dict)


def get_creator_apps(indexer: IndexerClient, creator_account: Account | str) -> AppLookup:
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

            def sort_by_round(transaction: dict) -> tuple[int, int]:
                confirmed = transaction["confirmed-round"]
                offset = transaction["intra-round-offset"]
                return confirmed, offset

            transactions.sort(key=sort_by_round, reverse=True)
            latest_transaction = transactions[0]
            app_updated_at_round = latest_transaction["confirmed-round"]

            def parse_note(metadata_b64: str | None) -> AppDeployMetaData | None:
                if not metadata_b64:
                    return None
                try:
                    return AppDeployMetaData.from_b64(metadata_b64)
                except json.decoder.JSONDecodeError:
                    return None

            create_metadata = parse_note(created_transaction.get("note"))
            update_metadata = parse_note(latest_transaction.get("note"))

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


def _replace_template_variable(program_lines: list[str], template_variable: str, value: str) -> tuple[list[str], int]:
    result: list[str] = []
    match_count = 0
    pattern = re.compile(rf"(\b)TMPL_{template_variable}(\b|$)")

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


def _add_deploy_template_variables(
    template_values: TemplateValueDict, allow_update: bool | None, allow_delete: bool | None
) -> None:
    if allow_update is not None:
        template_values[_UPDATABLE] = int(allow_update)
    if allow_delete is not None:
        template_values[_DELETABLE] = int(allow_delete)


def _strip_comments(program: str) -> str:
    lines = [x.split("//", maxsplit=1)[0] for x in program.splitlines()]
    return "\n".join(lines)


def _check_template_variables(approval_program: str, template_values: TemplateValueDict) -> None:
    approval_program = _strip_comments(approval_program)
    if UPDATABLE_TEMPLATE_NAME in approval_program and _UPDATABLE not in template_values:
        raise DeploymentFailedError(
            "allow_update must be specified if deploy time configuration of update is being used"
        )
    if DELETABLE_TEMPLATE_NAME in approval_program and _DELETABLE not in template_values:
        raise DeploymentFailedError(
            "allow_delete must be specified if deploy time configuration of delete is being used"
        )

    for template_variable_name in template_values:
        if template_variable_name not in approval_program:
            if template_variable_name == _UPDATABLE:
                raise DeploymentFailedError(
                    "allow_update must only be specified if deploy time configuration of update is being used"
                )
            if template_variable_name == _DELETABLE:
                raise DeploymentFailedError(
                    "allow_delete must only be specified if deploy time configuration of delete is being used"
                )
            logger.warning(f"{template_variable_name} not found in approval program, but variable was provided")


def replace_template_variables(program: str, template_values: TemplateValueDict) -> str:
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
