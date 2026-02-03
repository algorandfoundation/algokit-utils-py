from pydantic import RootModel


class ed25519PublicKeySchema(RootModel[list[int]]):
    pass
