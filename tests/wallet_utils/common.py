"""Common utilities for wallet_utils tests, adapted from TypeScript common.ts."""

from algokit_algod_client.models import AssetHolding
from mnemonic import Mnemonic

import algokit_algo25
from algokit_crypto import peikert_hd_wallet_generator
from algokit_transact import MultisigAccount, MultisigMetadata
from algokit_transact.signer import AddressWithSigners, generate_address_with_signers
from algokit_utils import AlgorandClient
from algokit_utils.assets.asset_manager import AssetInformation


def balance(algorand: AlgorandClient, account: AddressWithSigners | str) -> int:
    """Get ALGO balance for an account."""
    addr = account.addr if isinstance(account, AddressWithSigners) else account
    info = algorand.account.get_information(addr)
    return info.amount


def derive_hd_accounts_from_mnemonic(
    *, num_accounts: int, algorand: AlgorandClient | None = None
) -> list[AddressWithSigners]:
    """Generate random BIP39 mnemonic and derive HD accounts using Peikert scheme.

    Args:
        num_accounts: Number of accounts to derive
        algorand: Optional AlgorandClient to register accounts with for signing
    """
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=256)  # 24 words
    return derive_hd_accounts_from_bip39_mnemonic(mnemonic, num_accounts, algorand)


def derive_hd_accounts_from_bip39_mnemonic(
    mnemonic: str, num_accounts: int, algorand: AlgorandClient | None = None
) -> list[AddressWithSigners]:
    """Derive accounts from existing BIP39 mnemonic using Peikert scheme.

    Args:
        mnemonic: The BIP39 mnemonic string
        num_accounts: Number of accounts to derive
        algorand: Optional AlgorandClient to register accounts with for signing
    """
    mnemo = Mnemonic("english")
    seed = mnemo.to_seed(mnemonic)  # Returns 64-byte seed

    wallet = peikert_hd_wallet_generator(bytearray(seed))
    account_generator = wallet["account_generator"]

    accounts: list[AddressWithSigners] = []
    for i in range(num_accounts):
        generated = account_generator(i, 0)
        addr_with_signers = generate_address_with_signers(
            generated["ed25519_pubkey"],
            generated["raw_ed25519_signer"],
        )
        accounts.append(addr_with_signers)
        if algorand is not None:
            algorand.account.set_signer_from_account(addr_with_signers)

    return accounts


def derive_hd_accounts_from_algo25_mnemonic(
    mnemonic: str, num_accounts: int, algorand: AlgorandClient | None = None
) -> list[AddressWithSigners]:
    """Derive accounts from Algorand 25-word mnemonic using Peikert scheme.

    Args:
        mnemonic: The 25-word Algorand mnemonic string
        num_accounts: Number of accounts to derive
        algorand: Optional AlgorandClient to register accounts with for signing
    """
    seed = algokit_algo25.seed_from_mnemonic(mnemonic)
    # Algo25 seed is 32 bytes, need 64 bytes for HD wallet
    # Use the seed directly and pad or use as part of larger seed
    full_seed = bytearray(64)
    full_seed[:32] = seed

    wallet = peikert_hd_wallet_generator(full_seed)
    account_generator = wallet["account_generator"]

    accounts: list[AddressWithSigners] = []
    for i in range(num_accounts):
        generated = account_generator(i, 0)
        addr_with_signers = generate_address_with_signers(
            generated["ed25519_pubkey"],
            generated["raw_ed25519_signer"],
        )
        accounts.append(addr_with_signers)
        if algorand is not None:
            algorand.account.set_signer_from_account(addr_with_signers)

    return accounts


def generate_algo25_mnemonic() -> str:
    """Generate random 25-word Algorand mnemonic."""
    import os

    seed = os.urandom(32)
    return algokit_algo25.mnemonic_from_seed(seed)


def get_asset_balance(algorand: AlgorandClient, account: AddressWithSigners, asset_id: int) -> int:
    """Get balance of specific asset for account."""
    try:
        info = algorand.asset.get_account_information(account.addr, asset_id)
        return info.balance
    except Exception:
        return 0


def get_account_assets(algorand: AlgorandClient, account: AddressWithSigners) -> list[AssetHolding]:
    """Get all asset holdings for account."""
    info = algorand.client.algod.account_information(account.addr)
    return info.assets or []


def get_asset_info(algorand: AlgorandClient, asset_id: int) -> AssetInformation:
    """Get asset information by ID."""
    return algorand.asset.get_by_id(asset_id)


def create_multisig_account(
    accounts: list[AddressWithSigners],
    threshold: int,
    version: int = 1,
    sub_signers: list[AddressWithSigners] | None = None,
    algorand: AlgorandClient | None = None,
) -> MultisigAccount:
    """Create a MultisigAccount from a list of accounts.

    Args:
        accounts: List of accounts to use as signers
        threshold: Number of required signatures
        version: Multisig version (default 1)
        sub_signers: Subset of accounts that will actually sign
        algorand: Optional AlgorandClient to register accounts with for signing
    """
    addrs = [a.addr for a in accounts]
    metadata = MultisigMetadata(version=version, threshold=threshold, addrs=addrs)
    subs = sub_signers if sub_signers is not None else []
    multisig = MultisigAccount(params=metadata, sub_signers=subs)
    if algorand is not None:
        algorand.account.set_signer_from_account(multisig)
    return multisig
