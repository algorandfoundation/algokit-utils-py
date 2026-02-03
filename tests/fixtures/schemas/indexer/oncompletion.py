from typing import Any
from pydantic import BaseModel, ConfigDict


class OnCompletionSchema(BaseModel):
    """\[apan\] defines the what additional actions occur with the transaction.

    Valid types:
    * noop
    * optin
    * closeout
    * clear
    * update
    * delete"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")
