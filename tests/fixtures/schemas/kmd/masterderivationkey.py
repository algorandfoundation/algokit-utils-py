from pydantic import RootModel


class MasterDerivationKeySchema(RootModel[str]):
    """MasterDerivationKey is used to derive ed25519 keys for use in wallets"""

    pass
