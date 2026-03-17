from pydantic import RootModel


class SignatureSchema(RootModel[str]):
    pass
