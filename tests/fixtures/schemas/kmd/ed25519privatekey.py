from pydantic import RootModel


class ed25519PrivateKeySchema(RootModel[str]):
    pass
