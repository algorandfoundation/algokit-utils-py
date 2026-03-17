from pydantic import RootModel


class PublicKeySchema(RootModel[str]):
    pass
