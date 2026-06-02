"""Hierarchical Deterministic (HD) wallet generation using xhd-wallet-api."""

from collections.abc import Callable
from typing import Protocol, TypedDict, runtime_checkable

from xhd_wallet_api_py import (
    DerivationScheme,
    KeyContext,
    derive_path,
    from_seed,
    key_gen,
    public_key,
    raw_sign,
    seed_from_mnemonic,
)

from algokit_crypto.ed25519 import RawEd25519Signer

# Seed size for HD wallet generation
HD_WALLET_SEED_SIZE = 64

# BIP44 path constants for Algorand
BIP44_PURPOSE = 44
BIP44_COIN_TYPE = 283
BIP44_CHANGE = 0

# Hardening bit for BIP44 derivation
HARDENED_BIT = 0x80000000


def _harden(index: int) -> int:
    """Convert a normal index to a hardened index."""
    return index | HARDENED_BIT


# Type for BIP44 path tuple: (purpose', coin_type', account', change, index)
BIP44Path = tuple[int, int, int, int, int]


class HdAccountResult(TypedDict):
    """Result of HD account generation."""

    ed25519_pubkey: bytes
    """The ed25519 public key corresponding to the generated account and index (32 bytes)."""
    extended_private_key: bytearray
    """The extended ed25519 private key (96 bytes for scalar + prefix + chain code)."""
    bip44_path: BIP44Path
    """The BIP44 path used to derive the key for the generated account and index."""
    raw_ed25519_signer: RawEd25519Signer
    """A signer function that can sign bytes using the ed25519 secret key."""


HdAccountGenerator = Callable[[int, int], HdAccountResult]
"""Type for HD account generator functions.

Takes (account: int, index: int) and returns HdAccountResult.
"""


class HdWalletResult(TypedDict):
    """Result of HD wallet generation."""

    hd_root_key: bytearray
    """The HD root key (96 bytes extended private key)."""
    account_generator: HdAccountGenerator
    """Function to generate accounts from the HD wallet."""


HdWalletGenerator = Callable[[bytearray | None], HdWalletResult]
"""Type for HD wallet generator functions.

Takes optional seed bytes and returns HdWalletResult with root key and account generator.
"""


@runtime_checkable
class WrappedHdExtendedPrivateKey(Protocol):
    """Represents a 96-byte ``scalar || prefix || chain_code`` secret that can be unwrapped
    for short-lived use and optionally re-wrapped.

    The ``chain_code`` is NOT used for signing. It can, however, be used for key derivation.
    If your secret is only used for signing, it is recommended to only store the first 64 bytes
    in the secret store and then pad the secret to 96 bytes in the unwrap function.

    The ``wrap`` method is optional for implementations where wrapping is handled automatically
    (e.g., hardware wallets, keyring services).
    """

    def unwrap_hd_extended_private_key(self) -> bytearray: ...
    def wrap_hd_extended_private_key(self) -> None:
        """Optional method to re-wrap the extended private key after use.

        Defaults to no-op if not implemented.
        """
        ...


@runtime_checkable
class WrappedHdMnemonic(Protocol):
    """Represents a BIP39 mnemonic phrase for HD wallet derivation.

    The mnemonic is converted to a seed internally using the xhd-wallet-api's
    seed_from_mnemonic function, then used to derive the HD wallet.

    The ``wrap`` method is optional for implementations where wrapping is handled automatically
    (e.g., hardware wallets, keyring services).
    """

    def unwrap_hd_mnemonic(self) -> str: ...
    def wrap_hd_mnemonic(self) -> None:
        """Optional method to re-wrap the mnemonic after use.

        Defaults to no-op if not implemented.
        """
        ...


def hd_seed_from_mnemonic(mnemonic: str) -> bytearray:
    """Convert a BIP39 mnemonic phrase to a 64-byte seed.

    Args:
        mnemonic: A BIP39 mnemonic phrase (typically 12, 15, 18, 21, or 24 words).

    Returns:
        A 64-byte seed derived from the mnemonic using the xhd-wallet-api's
        seed_from_mnemonic function.
    """
    seed = seed_from_mnemonic(mnemonic)
    return bytearray(seed)


def hd_root_key_from_seed(seed: bytearray) -> bytearray:
    """Convert a 64-byte seed to a 96-byte HD extended private key root.

    Args:
        seed: A 64-byte seed.

    Returns:
        A 96-byte extended private key (root key).

    Raises:
        ValueError: If the seed is not 64 bytes.
    """
    if len(seed) != HD_WALLET_SEED_SIZE:
        raise ValueError(f"Seed must be {HD_WALLET_SEED_SIZE} bytes, got {len(seed)}")
    return from_seed(seed)


def hd_root_key_from_mnemonic(mnemonic: str) -> bytearray:
    """Convert a BIP39 mnemonic phrase directly to a 96-byte HD extended private key root.

    This is a convenience function that combines hd_seed_from_mnemonic and
    hd_root_key_from_seed.

    Args:
        mnemonic: A BIP39 mnemonic phrase.

    Returns:
        A 96-byte extended private key (root key).
    """
    seed = hd_seed_from_mnemonic(mnemonic)
    return hd_root_key_from_seed(seed)


def peikert_hd_wallet_generator(seed: bytearray | None = None) -> HdWalletResult:
    """Generate an HD wallet using the Peikert derivation scheme.

    Args:
        seed: Optional 64-byte seed for deterministic wallet generation.
            If not provided, a random seed will be generated.

    Returns:
        An HdWalletResult containing the HD root key and an account generator function.
    """
    import os

    if seed is None:
        seed = bytearray(os.urandom(HD_WALLET_SEED_SIZE))
    elif len(seed) != HD_WALLET_SEED_SIZE:
        raise ValueError(f"Seed must be {HD_WALLET_SEED_SIZE} bytes")

    root_key = from_seed(seed)

    def _account_generator(account: int, index: int) -> HdAccountResult:
        # Generate key using key_gen with Peikert derivation
        # Note: In TypeScript, account is passed directly and key_gen handles the context
        xprv_key = key_gen(
            root_key,
            KeyContext.Address,
            account,
            index,
            DerivationScheme.Peikert,
        )

        # Extract public key from the generated xprv
        ed25519_pubkey = public_key(xprv_key)

        # Construct BIP44 path (matching TypeScript implementation)
        bip44_path: BIP44Path = (
            _harden(BIP44_PURPOSE),
            _harden(BIP44_COIN_TYPE),
            _harden(account),
            BIP44_CHANGE,
            index,
        )

        # Derive the extended private key at the BIP44 path
        extended_private_key = derive_path(
            root_key,
            list(bip44_path),
            DerivationScheme.Peikert,
        )

        def raw_ed25519_signer(bytes_to_sign: bytes) -> bytes:
            """Sign bytes using the ed25519 secret key."""
            return raw_sign(
                root_key,
                list(bip44_path),
                bytes_to_sign,
                DerivationScheme.Peikert,
            )

        return {
            "ed25519_pubkey": ed25519_pubkey,
            "extended_private_key": extended_private_key,
            "bip44_path": bip44_path,
            "raw_ed25519_signer": raw_ed25519_signer,
        }

    return {
        "hd_root_key": root_key,
        "account_generator": _account_generator,
    }
