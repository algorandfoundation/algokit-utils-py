from pydantic import BaseModel, ConfigDict, Field


class ExportMultisigResponseSchema(BaseModel):
    """ExportMultisigResponse is the response to `POST /v1/multisig/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig_version: int = Field(alias="multisig_version")
    pks: "list[PublicKeySchema]" = Field(alias="pks")
    threshold: int = Field(alias="threshold")
