from typing import Any
from pydantic import BaseModel, ConfigDict


class HashtypeSchema(BaseModel):
    """The type of hash function used to create the proof, must be one of:
    * sha512_256
    * sha256"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")
