from pydantic import RootModel


class ed25519PublicKeySchema(RootModel[str]):
    pass
