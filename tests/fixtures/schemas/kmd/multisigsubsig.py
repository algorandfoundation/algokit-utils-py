from pydantic import BaseModel, ConfigDict, Field


class MultisigSubsigSchema(BaseModel):
    """MultisigSubsig is a struct that holds a pair of public key and signatures
    signatures may be empty"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    public_key: "PublicKeySchema" = Field(alias="pk")
    signature: "SignatureSchema | None" = Field(default=None, alias="s")
