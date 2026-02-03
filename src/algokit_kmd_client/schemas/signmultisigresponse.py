from pydantic import BaseModel, ConfigDict, Field


class SignMultisigResponseSchema(BaseModel):
    """SignMultisigResponse is the response to `POST /v1/multisig/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig: str = Field(default=None, alias="multisig")
