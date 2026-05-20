"""Wrapped-secret Ed25519 signing utilities.

Provides functions to derive Ed25519 signing keys from wrapped secrets,
with memory zeroing for security. Supports Ed25519 seeds, HD extended
private keys, HD mnemonics, and legacy Algorand mnemonics.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Protocol, runtime_checkable

import nacl.bindings
import nacl.signing
from exceptiongroup import ExceptionGroup
from xhd_wallet_api_py import public_key

from algokit_algo25 import seed_from_mnemonic
from algokit_crypto.ed25519 import ED25519_SEED_SIZE, Ed25519SigningKey, WrappedEd25519Seed
from algokit_crypto.hd import (
    BIP44_CHANGE,
    BIP44_COIN_TYPE,
    BIP44_PURPOSE,
    WrappedHdExtendedPrivateKey,
    WrappedHdMnemonic,
    hd_root_key_from_mnemonic,
)

ED25519_EXTENDED_PRIVATE_KEY_LENGTH = 96

_ED25519_ORDER = 0x1000000000000000000000000000000014DEF9DEA2F79CD65812631A5CF5D3ED

# Hardening bit for BIP44 derivation
_HARDENED_BIT = 0x80000000


@runtime_checkable
class WrappedLegacyMnemonic(Protocol):
    """Represents a legacy 25-word Algorand mnemonic phrase.

    The ``wrap`` method is optional for implementations where wrapping is handled automatically
    (e.g., hardware wallets, keyring services).
    """

    def unwrap_legacy_mnemonic(self) -> str: ...
    def wrap_legacy_mnemonic(self) -> None:
        """Optional method to re-wrap the mnemonic after use.

        Defaults to no-op if not implemented.
        """
        ...


WrappedEd25519Secret = WrappedEd25519Seed | WrappedHdExtendedPrivateKey | WrappedHdMnemonic | WrappedLegacyMnemonic


def _harden(index: int) -> int:
    """Convert a normal index to a hardened index."""
    return index | _HARDENED_BIT


def _assert_ed25519_secret_length(secret: bytearray | bytes, secret_type: str) -> None:
    if secret_type == "ed25519 seed":
        expected_length = ED25519_SEED_SIZE
    elif secret_type == "HD extended key":
        expected_length = ED25519_EXTENDED_PRIVATE_KEY_LENGTH
    else:
        raise ValueError(f"Unknown secret type: {secret_type}")

    if len(secret) != expected_length:
        raise ValueError(f"Expected unwrapped {secret_type} to be {expected_length} bytes, got {len(secret)}.")


def _raw_sign(extended_secret_key: bytearray, data: bytes) -> bytes:
    """Sign data using an HD extended secret key (first 64 bytes: scalar || prefix).

    Implements Ed25519 signing with a pre-derived scalar (no SHA-512 hashing of the
    secret key), matching the Peikert HD wallet derivation scheme.
    """
    scalar = int.from_bytes(extended_secret_key[:32], "little")
    k_r = bytes(extended_secret_key[32:64])

    # (1): pubKey = scalar * G
    pubkey = public_key(extended_secret_key)

    # (2): r = SHA512(kR || data) mod order
    r_hash = hashlib.sha512(k_r + data).digest()
    r = int.from_bytes(r_hash, "little") % _ED25519_ORDER

    # (3): R = r * G
    r_bytes = r.to_bytes(32, "little")
    r_point = nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(r_bytes)

    # (4): h = SHA512(R || pubkey || data) mod order
    h_hash = hashlib.sha512(r_point + pubkey + data).digest()
    h = int.from_bytes(h_hash, "little") % _ED25519_ORDER

    # (5): S = (r + h * scalar) mod order
    s = (r + h * scalar) % _ED25519_ORDER
    s_bytes = s.to_bytes(32, "little")

    return r_point + s_bytes


def _zero_secret(secret: bytearray | None) -> None:
    """Zero out a bytearray secret in memory."""
    if secret is not None:
        secret[:] = b"\x00" * len(secret)


def _get_wrap_function(wrapped: WrappedEd25519Secret) -> Callable[[], None]:
    """Get the appropriate wrap function for a wrapped secret.

    Returns a no-op function if the wrap method is not implemented.
    """
    # Use hasattr to check for unwrap methods to determine the type
    # This allows implementations without wrap methods to work
    if hasattr(wrapped, "unwrap_ed25519_seed"):
        return getattr(wrapped, "wrap_ed25519_seed", lambda: None)
    elif hasattr(wrapped, "unwrap_hd_extended_private_key"):
        return getattr(wrapped, "wrap_hd_extended_private_key", lambda: None)
    elif hasattr(wrapped, "unwrap_hd_mnemonic"):
        return getattr(wrapped, "wrap_hd_mnemonic", lambda: None)
    elif hasattr(wrapped, "unwrap_legacy_mnemonic"):
        return getattr(wrapped, "wrap_legacy_mnemonic", lambda: None)
    else:
        raise ValueError("Invalid WrappedEd25519Secret: unknown type")


def _unwrap_and_derive_pubkey(wrapped: WrappedEd25519Secret) -> tuple[bytes, bytearray | None]:
    """Unwrap the secret and derive the public key.

    Returns:
        A tuple of (public_key, secret_bytes) where secret_bytes may be None for mnemonic types.
    """
    # Use hasattr to check for unwrap methods to determine the type
    if hasattr(wrapped, "unwrap_ed25519_seed"):
        secret = wrapped.unwrap_ed25519_seed()
        _assert_ed25519_secret_length(secret, "ed25519 seed")
        signing_key = nacl.signing.SigningKey(bytes(secret))
        pubkey = bytes(signing_key.verify_key)
        return pubkey, secret

    elif hasattr(wrapped, "unwrap_hd_extended_private_key"):
        secret = wrapped.unwrap_hd_extended_private_key()
        _assert_ed25519_secret_length(secret, "HD extended key")
        pubkey = public_key(secret)
        return pubkey, secret

    elif hasattr(wrapped, "unwrap_hd_mnemonic"):
        mnemonic = wrapped.unwrap_hd_mnemonic()
        # Convert mnemonic to root key and derive account 0, index 0
        root_key = hd_root_key_from_mnemonic(mnemonic)
        # Derive the extended private key at the BIP44 path
        from xhd_wallet_api_py import DerivationScheme, derive_path

        bip44_path = [
            _harden(BIP44_PURPOSE),
            _harden(BIP44_COIN_TYPE),
            _harden(0),  # account 0
            BIP44_CHANGE,
            0,  # index 0
        ]
        extended_private_key = derive_path(root_key, bip44_path, DerivationScheme.Peikert)
        pubkey = public_key(extended_private_key)
        return pubkey, extended_private_key

    elif hasattr(wrapped, "unwrap_legacy_mnemonic"):
        mnemonic = wrapped.unwrap_legacy_mnemonic()
        seed = seed_from_mnemonic(mnemonic)
        signing_key = nacl.signing.SigningKey(seed)
        pubkey = bytes(signing_key.verify_key)
        # Return the seed as the secret to be zeroed
        return pubkey, bytearray(seed)

    else:
        raise ValueError("Invalid WrappedEd25519Secret: missing unwrap function")


def _unwrap_and_sign(wrapped: WrappedEd25519Secret, data: bytes) -> tuple[bytes, bytearray | None]:
    """Unwrap the secret and sign the data.

    Returns:
        A tuple of (signature, secret_bytes) where secret_bytes may be None for mnemonic types.
    """
    # Use hasattr to check for unwrap methods to determine the type
    if hasattr(wrapped, "unwrap_ed25519_seed"):
        secret = wrapped.unwrap_ed25519_seed()
        _assert_ed25519_secret_length(secret, "ed25519 seed")
        sk = nacl.signing.SigningKey(bytes(secret))
        signed = sk.sign(data)
        return signed.signature, secret

    elif hasattr(wrapped, "unwrap_hd_extended_private_key"):
        secret = wrapped.unwrap_hd_extended_private_key()
        _assert_ed25519_secret_length(secret, "HD extended key")
        signature = _raw_sign(secret, data)
        return signature, secret

    elif hasattr(wrapped, "unwrap_hd_mnemonic"):
        mnemonic = wrapped.unwrap_hd_mnemonic()
        # Convert mnemonic to root key and derive account 0, index 0
        root_key = hd_root_key_from_mnemonic(mnemonic)
        # Sign using the derived path
        from xhd_wallet_api_py import DerivationScheme, raw_sign

        bip44_path = [
            _harden(BIP44_PURPOSE),
            _harden(BIP44_COIN_TYPE),
            _harden(0),  # account 0
            BIP44_CHANGE,
            0,  # index 0
        ]
        signature = raw_sign(root_key, bip44_path, data, DerivationScheme.Peikert)
        # Return None for secret since we don't have direct access to it
        return signature, None

    elif hasattr(wrapped, "unwrap_legacy_mnemonic"):
        mnemonic = wrapped.unwrap_legacy_mnemonic()
        seed = seed_from_mnemonic(mnemonic)
        sk = nacl.signing.SigningKey(seed)
        signed = sk.sign(data)
        # Return the seed as the secret to be zeroed
        return signed.signature, bytearray(seed)

    else:
        raise ValueError("Invalid WrappedEd25519Secret: missing unwrap function")


def pynacl_ed25519_signing_key_from_wrapped_secret(wrapped: WrappedEd25519Secret) -> Ed25519SigningKey:
    """Create an Ed25519 signing key from a wrapped secret using PyNaCl.

    Supports Ed25519 seeds, HD extended private keys, HD mnemonics (BIP39),
    and legacy Algorand mnemonics (25-word).

    The unwrapped secret is zeroed out after use in ``finally`` blocks.

    Args:
        wrapped: A wrapped secret implementing one of the WrappedEd25519Secret protocols.

    Returns:
        An Ed25519SigningKey with the derived public key and a signer closure.

    Raises:
        ValueError: If the unwrapped secret has an invalid length.
        ExceptionGroup: If both the crypto operation and re-wrap fail.
    """
    # Determine wrap function
    wrap_function = _get_wrap_function(wrapped)

    # Derive public key
    pubkey: bytes | None = None
    pubkey_error: Exception | None = None
    wrap_error: Exception | None = None
    secret: bytearray | None = None
    try:
        pubkey, secret = _unwrap_and_derive_pubkey(wrapped)
    except Exception as e:
        pubkey_error = e
    finally:
        try:
            wrap_function()
        except Exception as e:
            wrap_error = e
        finally:
            _zero_secret(secret)

    if pubkey_error is not None and wrap_error is not None:
        raise ExceptionGroup(
            "Deriving Ed25519 public key failed and failed to re-wrap Ed25519 secret. Check both errors for details.",
            [pubkey_error, wrap_error],
        )

    if pubkey_error is not None:
        raise pubkey_error

    if wrap_error is not None:
        raise wrap_error

    if pubkey is None:
        raise RuntimeError("Deriving Ed25519 public key failed unexpectedly without an error.")

    # Build signer closure
    def signer(bytes_to_sign: bytes) -> bytes:
        signature: bytes | None = None
        signing_error: Exception | None = None
        sign_wrap_error: Exception | None = None
        sign_secret: bytearray | None = None
        try:
            signature, sign_secret = _unwrap_and_sign(wrapped, bytes_to_sign)
        except Exception as e:
            signing_error = e
        finally:
            try:
                wrap_function()
            except Exception as e:
                sign_wrap_error = e
            finally:
                _zero_secret(sign_secret)

        if signing_error is not None and sign_wrap_error is not None:
            raise ExceptionGroup(
                "Signing failed and failed to re-wrap Ed25519 secret. Check both errors for details.",
                [signing_error, sign_wrap_error],
            )

        if signing_error is not None:
            raise signing_error

        if sign_wrap_error is not None:
            raise sign_wrap_error

        if signature is None:
            raise RuntimeError("Signing failed unexpectedly without an error.")

        return signature

    return Ed25519SigningKey(
        ed25519_pubkey=pubkey,
        raw_ed25519_signer=signer,
    )


ed25519_signing_key_from_wrapped_secret = pynacl_ed25519_signing_key_from_wrapped_secret
"""Default function to create an Ed25519 signing key from a wrapped secret.

Currently uses the PyNaCl implementation. This may change in the future.
To explicitly use the PyNaCl implementation, use ``pynacl_ed25519_signing_key_from_wrapped_secret``.
"""
