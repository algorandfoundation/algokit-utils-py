from pydantic import RootModel


class PrivateKeySchema(RootModel[str]):
    pass
