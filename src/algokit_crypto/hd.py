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
)

from algokit_crypto.ed25519 import RawEd25519Signer

# Seed size for HD wallet generation (TypeScript uses 32 bytes)
HD_WALLET_SEED_SIZE = 32

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


HdWalletGenerator = Callable[[bytes | None], HdWalletResult]
"""Type for HD wallet generator functions.

Takes optional seed bytes and returns HdWalletResult with root key and account generator.
"""


@runtime_checkable
class WrappedHdExtendedPrivateKey(Protocol):
    """Represents a 96-byte ``scalar || prefix || chain_code`` secret that can be unwrapped
    for short-lived use and then re-wrapped.

    The ``chain_code`` is NOT used for signing. It can, however, be used for key derivation.
    If your secret is only used for signing, it is recommended to only store the first 64 bytes
    in the secret store and then pad the secret to 96 bytes in the unwrap function.
    """

    def unwrap_hd_extended_private_key(self) -> bytearray: ...
    def wrap_hd_extended_private_key(self) -> None: ...

def peikert_hd_wallet_generator(seed: bytearray | None = None) -> HdWalletResult:
    """Generate an HD wallet using the Peikert derivation scheme.

    Args:
        seed: Optional 32-byte seed for deterministic wallet generation.
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
