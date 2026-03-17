from pydantic import RootModel


class ed25519SignatureSchema(RootModel[str]):
    pass
