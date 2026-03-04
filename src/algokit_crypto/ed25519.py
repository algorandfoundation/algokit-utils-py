"""Ed25519 signature verification and key generation utilities."""

from collections.abc import Callable
from typing import Protocol, TypedDict

import nacl.exceptions
import nacl.signing

ED25519_SEED_SIZE = 32
"""Size of ed25519 seed in bytes."""

RawEd25519Verifier = Callable[[bytes, bytes, bytes], bool]
"""Type for raw ed25519 signature verifier functions.

Takes (signature: bytes, message: bytes, pubkey: bytes) and returns bool.
"""

RawEd25519Signer = Callable[[bytes], bytes]
"""Type for raw ed25519 signer functions.

Takes bytes to sign and returns the signature bytes.
"""


class Ed25519Keypair(TypedDict):
    """Result of ed25519 key generation."""

    ed25519_pubkey: bytes
    ed25519_secret_key: bytes
    raw_ed25519_signer: RawEd25519Signer


class Ed25519Generator(Protocol):
    """Protocol for ed25519 keypair generator functions.

    Takes optional seed bytes and returns Ed25519Keypair with pubkey, secret key, and signer.
    """

    def __call__(self, seed: bytes | None = None) -> Ed25519Keypair: ...


def pynacl_ed25519_verifier(signature: bytes, message: bytes, pubkey: bytes) -> bool:
    """Verify an ed25519 signature using PyNaCl (libsodium) implementation.

    Args:
        signature: The ed25519 signature bytes (64 bytes).
        message: The original message that was signed.
        pubkey: The ed25519 public key bytes (32 bytes).

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        verify_key = nacl.signing.VerifyKey(pubkey)
        verify_key.verify(message, signature)
        return True
    except nacl.exceptions.BadSignatureError:
        return False


# Default verifier uses the pynacl implementation
ed25519_verifier: RawEd25519Verifier = pynacl_ed25519_verifier
"""Default ed25519 signature verifier.

Currently uses the PyNaCl implementation. This may change in the future.
To explicitly use the PyNaCl implementation, use `pynacl_ed25519_verifier`.
"""


def pynacl_ed25519_generator(seed: bytes | None = None) -> Ed25519Keypair:
    """Generate an ed25519 keypair and raw signer using PyNaCl (libsodium).

    Args:
        seed: Optional 32-byte seed for deterministic key generation.
            If not provided, a random keypair will be generated.

    Returns:
        An Ed25519Keypair containing the public key (32 bytes), secret key (32 bytes),
        and a raw signer function.
    """
    if seed is not None:
        # Use provided seed (must be 32 bytes for ed25519)
        if len(seed) != ED25519_SEED_SIZE:
            raise ValueError(f"Seed must be {ED25519_SEED_SIZE} bytes for ed25519 key generation")
        signing_key = nacl.signing.SigningKey(seed)
    else:
        # Generate random keypair
        signing_key = nacl.signing.SigningKey.generate()

    # Get the public key
    verify_key = signing_key.verify_key
    ed25519_pubkey = bytes(verify_key)

    def raw_ed25519_signer(bytes_to_sign: bytes) -> bytes:
        """Sign bytes using the ed25519 secret key."""
        signed = signing_key.sign(bytes_to_sign)
        return signed.signature

    return {
        "ed25519_pubkey": ed25519_pubkey,
        "ed25519_secret_key": signing_key.encode(),
        "raw_ed25519_signer": raw_ed25519_signer,
    }


# Default generator uses the pynacl implementation
ed25519_generator: Ed25519Generator = pynacl_ed25519_generator
"""Default ed25519 keypair generator.

Currently uses the PyNaCl implementation. This may change in the future.
To explicitly use the PyNaCl implementation, use `pynacl_ed25519_generator`.
"""
