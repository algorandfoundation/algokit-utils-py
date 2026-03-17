from pydantic import RootModel


class HashtypeSchema(RootModel[str]):
    """The type of hash function used to create the proof, must be one of:
    * sha512_256
    * sha256"""

    pass
