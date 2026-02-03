from typing import Any
from pydantic import RootModel


class ed25519SignatureSchema(RootModel[list[int]]):
    pass
