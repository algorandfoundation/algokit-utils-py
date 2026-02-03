from pydantic import BaseModel, ConfigDict, Field


class TransactionApplicationSchema(BaseModel):
    """Fields for application transactions.

    Definition:
    data/transactions/application.go : ApplicationCallTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_id: int = Field(default=None, alias="application-id")
    on_completion: "OnCompletionSchema" = Field(default=None, alias="on-completion")
    application_args: list[str] | None = Field(default=None, alias="application-args")
    access: "list[ResourceRefSchema] | None" = Field(default=None, alias="access")
    accounts: list[str] | None = Field(default=None, alias="accounts")
    box_references: "list[BoxReferenceSchema] | None" = Field(default=None, alias="box-references")
    foreign_apps: list[int] | None = Field(default=None, alias="foreign-apps")
    foreign_assets: list[int] | None = Field(default=None, alias="foreign-assets")
    local_state_schema: "StateSchemaSchema | None" = Field(default=None, alias="local-state-schema")
    global_state_schema: "StateSchemaSchema | None" = Field(default=None, alias="global-state-schema")
    approval_program: str | None = Field(default=None, alias="approval-program")
    clear_state_program: str | None = Field(default=None, alias="clear-state-program")
    extra_program_pages: int | None = Field(default=None, ge=0, le=3, alias="extra-program-pages")
    reject_version: int | None = Field(default=None, alias="reject-version")
