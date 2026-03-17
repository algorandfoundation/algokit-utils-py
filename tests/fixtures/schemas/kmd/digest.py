from pydantic import RootModel


class DigestSchema(RootModel[list[int]]):
    pass
