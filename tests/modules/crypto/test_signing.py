"""Tests for wrapped-secret Ed25519 signing, mirroring crypto_ts/signer.spec.ts."""

import os

import nacl.signing
import pytest

from algokit_crypto import (
    ed25519_verifier,
    pynacl_ed25519_generator,
    pynacl_ed25519_signing_key_from_wrapped_secret,
    peikert_hd_wallet_generator,
)
from algokit_crypto.signing import _ExceptionGroup


class TestSigningBasics:
    """Basic signing and verification tests."""

    def test_generate_and_verify_with_pynacl(self) -> None:
        """Generate a keypair, sign, and verify using PyNaCl directly."""
        signing_key = nacl.signing.SigningKey.generate()
        pubkey = bytes(signing_key.verify_key)
        message = b"hello world"
        signed = signing_key.sign(message)
        signature = signed.signature

        assert ed25519_verifier(signature, message, pubkey) is True
        assert ed25519_verifier(signature, b"wrong message", pubkey) is False

    def test_generate_and_verify_with_generator(self) -> None:
        """Generate a keypair using pynacl_ed25519_generator, sign, and verify."""
        keypair = pynacl_ed25519_generator()
        message = b"test message"
        signature = keypair["raw_ed25519_signer"](message)

        assert ed25519_verifier(signature, message, keypair["ed25519_pubkey"]) is True

    def test_hd_wallet_sign_and_verify(self) -> None:
        """Generate an HD wallet, sign with HD signer, verify with ed25519_verifier."""
        wallet = peikert_hd_wallet_generator()
        account = wallet["account_generator"](0, 0)
        message = b"HD signing test"
        signature = account["raw_ed25519_signer"](message)

        assert ed25519_verifier(signature, message, account["ed25519_pubkey"]) is True


class TestWrappedSeedSigning:
    """Tests for wrapped Ed25519 seed signing."""

    def test_wrapped_seed_signing(self) -> None:
        """Create a wrapped seed, get signing key, sign, and verify."""
        seed = bytearray(os.urandom(32))

        class WrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                return bytearray(seed)

            def wrap_ed25519_seed(self) -> None:
                pass

        signing_key = pynacl_ed25519_signing_key_from_wrapped_secret(WrappedSeed())
        message = b"wrapped seed test"
        signature = signing_key["raw_ed25519_signer"](message)

        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True

    def test_wrapped_seed_rejects_invalid_length_pubkey(self) -> None:
        """31-byte seed should raise ValueError during pubkey derivation."""

        class BadWrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                return bytearray(31)

            def wrap_ed25519_seed(self) -> None:
                pass

        with pytest.raises(ValueError, match="Expected unwrapped ed25519 seed to be 32 bytes, got 31."):
            pynacl_ed25519_signing_key_from_wrapped_secret(BadWrappedSeed())

    def test_wrapped_seed_rejects_invalid_length_signing(self) -> None:
        """Second unwrap returns 31 bytes, should raise ValueError during signing."""
        seed = bytearray(os.urandom(32))
        unwrap_count = 0

        class BadSignWrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                nonlocal unwrap_count
                unwrap_count += 1
                if unwrap_count == 1:
                    return bytearray(seed)
                return bytearray(31)

            def wrap_ed25519_seed(self) -> None:
                pass

        signing_key = pynacl_ed25519_signing_key_from_wrapped_secret(BadSignWrappedSeed())

        with pytest.raises(ValueError, match="Expected unwrapped ed25519 seed to be 32 bytes, got 31."):
            signing_key["raw_ed25519_signer"](b"\x01\x02\x03")

    def test_wrapped_seed_reports_both_pubkey_and_wrap_failures(self) -> None:
        """Both unwrap and wrap fail; error should contain both messages."""

        class BothFailWrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                raise RuntimeError("unwrap failed")

            def wrap_ed25519_seed(self) -> None:
                raise RuntimeError("wrap failed")

        with pytest.raises(
            _ExceptionGroup,
            match="Deriving Ed25519 public key failed and failed to re-wrap Ed25519 secret",
        ):
            pynacl_ed25519_signing_key_from_wrapped_secret(BothFailWrappedSeed())

    def test_wrapped_seed_reports_both_signing_and_wrap_failures(self) -> None:
        """Both signing (unwrap) and wrap fail; error should contain both messages."""
        seed = bytearray(os.urandom(32))
        unwrap_should_fail = False
        wrap_should_fail = False

        class FailableWrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                if unwrap_should_fail:
                    raise RuntimeError("unwrap failed")
                return bytearray(seed)

            def wrap_ed25519_seed(self) -> None:
                if wrap_should_fail:
                    raise RuntimeError("wrap failed")

        signing_key = pynacl_ed25519_signing_key_from_wrapped_secret(FailableWrappedSeed())

        unwrap_should_fail = True
        wrap_should_fail = True

        with pytest.raises(
            _ExceptionGroup,
            match="Signing failed and failed to re-wrap Ed25519 secret",
        ):
            signing_key["raw_ed25519_signer"](b"\x01\x02\x03")

    def test_wrapped_seed_zeroes_secret_after_signing(self) -> None:
        """The bytearray secret should be zeroed after successful signing."""
        seed = bytearray(os.urandom(32))
        returned_secret: bytearray | None = None

        class ZeroCheckWrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                nonlocal returned_secret
                returned_secret = bytearray(seed)
                return returned_secret

            def wrap_ed25519_seed(self) -> None:
                pass

        signing_key = pynacl_ed25519_signing_key_from_wrapped_secret(ZeroCheckWrappedSeed())
        signing_key["raw_ed25519_signer"](b"\x0a\x14\x1e")

        assert returned_secret is not None
        assert all(b == 0 for b in returned_secret)

    def test_wrapped_seed_zeroes_secret_after_failed_wrap(self) -> None:
        """The bytearray secret should still be zeroed even if wrap fails."""
        seed = bytearray(os.urandom(32))
        unwrap_count = 0
        wrap_count = 0
        returned_secret: bytearray | None = None

        class ZeroOnFailWrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                nonlocal unwrap_count, returned_secret
                unwrap_count += 1
                if unwrap_count == 1:
                    return bytearray(seed)
                returned_secret = bytearray(seed)
                return returned_secret

            def wrap_ed25519_seed(self) -> None:
                nonlocal wrap_count
                wrap_count += 1
                if wrap_count > 1:
                    raise RuntimeError("wrap failed")

        signing_key = pynacl_ed25519_signing_key_from_wrapped_secret(ZeroOnFailWrappedSeed())

        with pytest.raises(RuntimeError, match="wrap failed"):
            signing_key["raw_ed25519_signer"](b"\x01\x02\x03")

        assert returned_secret is not None
        assert all(b == 0 for b in returned_secret)


class TestWrappedHdExtendedKeySigning:
    """Tests for wrapped HD extended private key signing."""

    def test_wrapped_hd_extended_key_signing(self) -> None:
        """Create a wrapped HD extended key, get signing key, sign, and verify."""
        wallet = peikert_hd_wallet_generator()
        account = wallet["account_generator"](0, 0)
        extended_key = bytearray(account["extended_private_key"])

        class WrappedHdKey:
            def unwrap_hd_extended_private_key(self) -> bytearray:
                return bytearray(extended_key)

            def wrap_hd_extended_private_key(self) -> None:
                pass

        signing_key = pynacl_ed25519_signing_key_from_wrapped_secret(WrappedHdKey())
        message = b"wrapped HD key test"
        signature = signing_key["raw_ed25519_signer"](message)

        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True

    def test_wrapped_hd_extended_key_rejects_invalid_length(self) -> None:
        """95-byte key should raise ValueError."""

        class BadWrappedHdKey:
            def unwrap_hd_extended_private_key(self) -> bytearray:
                return bytearray(95)

            def wrap_hd_extended_private_key(self) -> None:
                pass

        with pytest.raises(ValueError, match="Expected unwrapped HD extended key to be 96 bytes, got 95."):
            pynacl_ed25519_signing_key_from_wrapped_secret(BadWrappedHdKey())
