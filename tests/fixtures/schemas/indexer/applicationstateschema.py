from pydantic import BaseModel, ConfigDict, Field


class ApplicationStateSchemaSchema(BaseModel):
    """Specifies maximums on the number of each type that may be stored."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    num_uints: int = Field(ge=0, le=64, alias="num-uint")
    num_byte_slices: int = Field(ge=0, le=64, alias="num-byte-slice")
