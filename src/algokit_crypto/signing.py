"""Wrapped-secret Ed25519 signing utilities.

Provides functions to derive Ed25519 signing keys from wrapped secrets,
with memory zeroing for security. Supports both standard Ed25519 seeds
and HD extended private keys.
"""

from __future__ import annotations

import builtins
import hashlib
import sys

import nacl.bindings
import nacl.signing
from xhd_wallet_api_py import public_key

if sys.version_info >= (3, 11):
    _ExceptionGroupError = builtins.ExceptionGroup
else:

    class _ExceptionGroupError(Exception):
        """Backport of ExceptionGroup for Python 3.10."""

        def __init__(self, message: str, exceptions: list[BaseException]) -> None:
            super().__init__(message)
            self.exceptions = exceptions


from algokit_crypto.ed25519 import Ed25519SigningKey, WrappedEd25519Seed
from algokit_crypto.hd import WrappedHdExtendedPrivateKey

WrappedEd25519Secret = WrappedEd25519Seed | WrappedHdExtendedPrivateKey

ED25519_SEED_LENGTH = 32
ED25519_EXTENDED_PRIVATE_KEY_LENGTH = 96

_ED25519_ORDER = 0x1000000000000000000000000000000014DEF9DEA2F79CD65812631A5CF5D3ED


def _assert_ed25519_secret_length(secret: bytearray | bytes, secret_type: str) -> None:
    if secret_type == "ed25519 seed":
        expected_length = ED25519_SEED_LENGTH
    elif secret_type == "HD extended key":
        expected_length = ED25519_EXTENDED_PRIVATE_KEY_LENGTH
    else:
        raise ValueError(f"Unknown secret type: {secret_type}")

    if len(secret) != expected_length:
        raise ValueError(f"Expected unwrapped {secret_type} to be {expected_length} bytes, got {len(secret)}.")


def _raw_sign(extended_secret_key: bytes | bytearray, data: bytes) -> bytes:
    """Sign data using an HD extended secret key (first 64 bytes: scalar || prefix).

    Implements Ed25519 signing with a pre-derived scalar (no SHA-512 hashing of the
    secret key), matching the Peikert HD wallet derivation scheme.
    """
    scalar = int.from_bytes(extended_secret_key[:32], "little")
    k_r = bytes(extended_secret_key[32:64])

    # (1): pubKey = scalar * G
    pubkey = public_key(bytes(extended_secret_key))

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


def pynacl_ed25519_signing_key_from_wrapped_secret(wrapped: WrappedEd25519Secret) -> Ed25519SigningKey:
    """Create an Ed25519 signing key from a wrapped secret using PyNaCl.

    Supports both standard Ed25519 seeds (via WrappedEd25519Seed) and
    HD extended private keys (via WrappedHdExtendedPrivateKey).

    The unwrapped secret is zeroed out after use in ``finally`` blocks.

    Args:
        wrapped: A wrapped secret provider implementing either WrappedEd25519Seed
            or WrappedHdExtendedPrivateKey.

    Returns:
        An Ed25519SigningKey with the derived public key and a signer closure.

    Raises:
        ValueError: If the unwrapped secret has an invalid length.
        _ExceptionGroupError: If both the crypto operation and re-wrap fail.
    """
    # Determine wrap function
    if isinstance(wrapped, WrappedEd25519Seed):
        wrap_function = wrapped.wrap_ed25519_seed
    elif isinstance(wrapped, WrappedHdExtendedPrivateKey):
        wrap_function = wrapped.wrap_hd_extended_private_key
    else:
        raise ValueError("Invalid WrappedEd25519Secret: missing wrap function")

    # Derive public key
    pubkey: bytes | None = None
    pubkey_error: BaseException | None = None
    wrap_error: BaseException | None = None
    secret: bytearray | None = None
    try:
        if isinstance(wrapped, WrappedEd25519Seed):
            secret = wrapped.unwrap_ed25519_seed()
            _assert_ed25519_secret_length(secret, "ed25519 seed")
            signing_key = nacl.signing.SigningKey(bytes(secret))
            pubkey = bytes(signing_key.verify_key)
        elif isinstance(wrapped, WrappedHdExtendedPrivateKey):
            secret = wrapped.unwrap_hd_extended_private_key()
            _assert_ed25519_secret_length(secret, "HD extended key")
            pubkey = public_key(bytes(secret))
        else:
            raise ValueError("Invalid WrappedEd25519Secret: missing unwrap function")
    except BaseException as e:
        pubkey_error = e
    finally:
        try:
            wrap_function()
        except BaseException as e:
            wrap_error = e
        finally:
            _zero_secret(secret)

    if pubkey_error is not None and wrap_error is not None:
        raise _ExceptionGroupError(
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
        signing_error: BaseException | None = None
        sign_wrap_error: BaseException | None = None
        sign_secret: bytearray | None = None
        try:
            if isinstance(wrapped, WrappedEd25519Seed):
                sign_secret = wrapped.unwrap_ed25519_seed()
                _assert_ed25519_secret_length(sign_secret, "ed25519 seed")
                sk = nacl.signing.SigningKey(bytes(sign_secret))
                signed = sk.sign(bytes_to_sign)
                signature = signed.signature
            elif isinstance(wrapped, WrappedHdExtendedPrivateKey):
                sign_secret = wrapped.unwrap_hd_extended_private_key()
                _assert_ed25519_secret_length(sign_secret, "HD extended key")
                signature = _raw_sign(sign_secret, bytes_to_sign)
            else:
                raise ValueError("Invalid WrappedEd25519Secret: missing unwrap function")
        except BaseException as e:
            signing_error = e
        finally:
            try:
                wrap_function()
            except BaseException as e:
                sign_wrap_error = e
            finally:
                _zero_secret(sign_secret)

        if signing_error is not None and sign_wrap_error is not None:
            raise _ExceptionGroupError(
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
