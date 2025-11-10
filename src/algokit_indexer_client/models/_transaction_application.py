# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import enum_value, nested, wire

from ._box_reference import BoxReference
from ._on_completion import OnCompletion
from ._resource_ref import ResourceRef
from ._serde_helpers import decode_bytes_base64, decode_model_sequence, encode_bytes_base64, encode_model_sequence
from ._state_schema import StateSchema


@dataclass(slots=True)
class TransactionApplication:
    """
    Fields for application transactions.

    Definition:
    data/transactions/application.go : ApplicationCallTxnFields
    """

    application_id: int = field(
        metadata=wire("application-id"),
    )
    on_completion: OnCompletion = field(
        metadata=enum_value("on-completion", OnCompletion),
    )
    access: list[ResourceRef] | None = field(
        default=None,
        metadata=wire(
            "access",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: ResourceRef, raw),
        ),
    )
    accounts: list[str] | None = field(
        default=None,
        metadata=wire("accounts"),
    )
    application_args: list[str] | None = field(
        default=None,
        metadata=wire("application-args"),
    )
    approval_program: bytes | None = field(
        default=None,
        metadata=wire(
            "approval-program",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    box_references: list[BoxReference] | None = field(
        default=None,
        metadata=wire(
            "box-references",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: BoxReference, raw),
        ),
    )
    clear_state_program: bytes | None = field(
        default=None,
        metadata=wire(
            "clear-state-program",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    extra_program_pages: int | None = field(
        default=None,
        metadata=wire("extra-program-pages"),
    )
    foreign_apps: list[int] | None = field(
        default=None,
        metadata=wire("foreign-apps"),
    )
    foreign_assets: list[int] | None = field(
        default=None,
        metadata=wire("foreign-assets"),
    )
    global_state_schema: StateSchema | None = field(
        default=None,
        metadata=nested("global-state-schema", lambda: StateSchema),
    )
    local_state_schema: StateSchema | None = field(
        default=None,
        metadata=nested("local-state-schema", lambda: StateSchema),
    )
    reject_version: int | None = field(
        default=None,
        metadata=wire("reject-version"),
    )
