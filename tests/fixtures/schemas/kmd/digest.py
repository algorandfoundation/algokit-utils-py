from pydantic import RootModel


class DigestSchema(RootModel[str]):
    pass
