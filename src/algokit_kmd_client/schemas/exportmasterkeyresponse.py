from pydantic import BaseModel, ConfigDict, Field


class ExportMasterKeyResponseSchema(BaseModel):
    """ExportMasterKeyResponse is the response to `POST /v1/master-key/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    master_derivation_key: "MasterDerivationKeySchema" = Field(default=None, alias="master_derivation_key")
