# AUTO-GENERATED: oas_generator


from enum import Enum


class Hashtype(Enum):
    """
    The type of hash function used to create the proof, must be one of:
    * sha512_256
    * sha256
    """

    SHA512_256 = "sha512_256"
    SHA256 = "sha256"
