from pydantic import BaseModel, ConfigDict, Field


class HbProofFieldsSchema(BaseModel):
    r"""\[hbprf\] HbProof is a signature using HeartbeatAddress's partkey, thereby showing it is online."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hb_sig: str | None = Field(default=None, alias="hb-sig")
    hb_pk: str | None = Field(default=None, alias="hb-pk")
    hb_pk2: str | None = Field(default=None, alias="hb-pk2")
    hb_pk1sig: str | None = Field(default=None, alias="hb-pk1sig")
    hb_pk2sig: str | None = Field(default=None, alias="hb-pk2sig")
