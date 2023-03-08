import dataclasses


@dataclasses.dataclass
class Account:
    private_key: str
    address: str
