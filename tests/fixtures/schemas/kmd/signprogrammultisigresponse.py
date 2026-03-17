from pydantic import BaseModel, ConfigDict, Field


class SignProgramMultisigResponseSchema(BaseModel):
    """SignProgramMultisigResponse is the response to `POST /v1/multisig/signdata`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig: str = Field(alias="multisig")
