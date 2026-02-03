from typing import Any
from pydantic import RootModel


class ParticipationKeysResponseSchema(RootModel[list["ParticipationKeySchema"]]):
    pass
