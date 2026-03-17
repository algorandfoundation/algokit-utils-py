from pydantic import BaseModel, ConfigDict, Field


class SignProgramRequestSchema(BaseModel):
    """The request for `POST /v1/program/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    program: str = Field(alias="data")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")
