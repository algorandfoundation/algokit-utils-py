import dataclasses

import algosdk
from algosdk.atomic_transaction_composer import AccountTransactionSigner

DISPENSER_ACCOUNT_NAME = "DISPENSER"


@dataclasses.dataclass(kw_only=True)
class Account:
    """Holds the private_key and address for an account"""

    private_key: str
    """Base64 encoded private key"""
    address: str = dataclasses.field(default="")
    """Address for this account"""

    def __post_init__(self) -> None:
        if not self.address:
            self.address = algosdk.account.address_from_private_key(self.private_key)  # type: ignore[arg-type]

    @property
    def public_key(self) -> bytes:
        """The public key for this account"""
        public_key = algosdk.encoding.decode_address(self.address)
        assert isinstance(public_key, bytes)
        return public_key

    @property
    def signer(self) -> AccountTransactionSigner:
        """An AccountTransactionSigner for this account"""
        return AccountTransactionSigner(self.private_key)

    @staticmethod
    def new_account() -> "Account":
        private_key, address = algosdk.account.generate_account()
        return Account(private_key=private_key)
