"""Tests for wrapped secret protocols and AccountManager.from_secret."""

import os

import pytest

from algokit_algo25 import mnemonic_from_seed
from algokit_crypto import (
    WrappedHdMnemonic,
    WrappedLegacyMnemonic,
    ed25519_signing_key_from_wrapped_secret,
    ed25519_verifier,
    hd_root_key_from_mnemonic,
    hd_seed_from_mnemonic,
    pynacl_ed25519_generator,
)
from algokit_utils.algorand import AlgorandClient


class TestWrappedHdMnemonicSigning:
    """Tests for wrapped HD mnemonic signing."""

    def test_wrapped_hd_mnemonic_signing(self) -> None:
        """Create a wrapped HD mnemonic, get signing key, sign, and verify."""
        # Generate a random seed and convert to mnemonic
        seed = os.urandom(64)
        # For testing, we'll use a class that wraps the seed derived HD mnemonic

        class WrappedHdMnemonicImpl:
            def __init__(self, mnemonic: str) -> None:
                self._mnemonic = mnemonic

            def unwrap_hd_mnemonic(self) -> str:
                return self._mnemonic

            def wrap_hd_mnemonic(self) -> None:
                pass

        # Generate an HD wallet from a seed and get account 0
        from algokit_crypto import peikert_hd_wallet_generator

        seed_bytes = bytearray(seed)
        wallet = peikert_hd_wallet_generator(seed_bytes)
        _ = wallet["account_generator"](0, 0)  # Verify wallet works

        # Create a wrapped HD mnemonic using the same seed
        # (Note: xhd-wallet-api doesn't expose mnemonic generation, so we test with seed directly)
        # For this test, we'll use a known BIP39 mnemonic
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        wrapped = WrappedHdMnemonicImpl(test_mnemonic)

        # Verify it's recognized as a WrappedHdMnemonic
        assert isinstance(wrapped, WrappedHdMnemonic)

        # Get signing key
        signing_key = ed25519_signing_key_from_wrapped_secret(wrapped)
        message = b"wrapped HD mnemonic test"
        signature = signing_key["raw_ed25519_signer"](message)

        # Verify
        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True

    def test_wrapped_hd_mnemonic_without_wrap_method(self) -> None:
        """HD mnemonic without wrap method should still work."""

        class WrappedHdMnemonicNoWrap:
            def __init__(self, mnemonic: str) -> None:
                self._mnemonic = mnemonic

            def unwrap_hd_mnemonic(self) -> str:
                return self._mnemonic

            # Note: no wrap_hd_mnemonic method

        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        wrapped = WrappedHdMnemonicNoWrap(test_mnemonic)

        # Should work without wrap method
        signing_key = ed25519_signing_key_from_wrapped_secret(wrapped)
        message = b"test without wrap"
        signature = signing_key["raw_ed25519_signer"](message)

        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True


class TestWrappedLegacyMnemonicSigning:
    """Tests for wrapped legacy mnemonic signing."""

    def test_wrapped_legacy_mnemonic_signing(self) -> None:
        """Create a wrapped legacy mnemonic, get signing key, sign, and verify."""
        # Generate a random keypair and get its mnemonic
        keypair = pynacl_ed25519_generator()
        seed = keypair["ed25519_secret_key"][:32]
        mnemonic = mnemonic_from_seed(seed)

        class WrappedLegacyMnemonicImpl:
            def __init__(self, mnemonic: str) -> None:
                self._mnemonic = mnemonic

            def unwrap_legacy_mnemonic(self) -> str:
                return self._mnemonic

            def wrap_legacy_mnemonic(self) -> None:
                pass

        wrapped = WrappedLegacyMnemonicImpl(mnemonic)

        # Verify it's recognized as a WrappedLegacyMnemonic
        assert isinstance(wrapped, WrappedLegacyMnemonic)

        # Get signing key
        signing_key = ed25519_signing_key_from_wrapped_secret(wrapped)
        message = b"wrapped legacy mnemonic test"
        signature = signing_key["raw_ed25519_signer"](message)

        # Verify signature
        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True

        # Verify the public key matches the original
        assert signing_key["ed25519_pubkey"] == keypair["ed25519_pubkey"]

    def test_wrapped_legacy_mnemonic_without_wrap_method(self) -> None:
        """Legacy mnemonic without wrap method should still work."""
        # Generate a random keypair and get its mnemonic
        keypair = pynacl_ed25519_generator()
        seed = keypair["ed25519_secret_key"][:32]
        mnemonic = mnemonic_from_seed(seed)

        class WrappedLegacyMnemonicNoWrap:
            def __init__(self, mnemonic: str) -> None:
                self._mnemonic = mnemonic

            def unwrap_legacy_mnemonic(self) -> str:
                return self._mnemonic

            # Note: no wrap_legacy_mnemonic method

        wrapped = WrappedLegacyMnemonicNoWrap(mnemonic)

        # Should work without wrap method
        signing_key = ed25519_signing_key_from_wrapped_secret(wrapped)
        message = b"test without wrap"
        signature = signing_key["raw_ed25519_signer"](message)

        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True


class TestHdHelperFunctions:
    """Tests for HD wallet helper functions."""

    def test_hd_seed_from_mnemonic(self) -> None:
        """Test converting mnemonic to seed."""
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        seed = hd_seed_from_mnemonic(mnemonic)

        # Should be 64 bytes
        assert len(seed) == 64

    def test_hd_root_key_from_mnemonic(self) -> None:
        """Test converting mnemonic directly to root key."""
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        root_key = hd_root_key_from_mnemonic(mnemonic)

        # Should be 96 bytes
        assert len(root_key) == 96

    def test_hd_seed_from_mnemonic_invalid_length(self) -> None:
        """Test that invalid seed length raises ValueError."""
        from algokit_crypto.hd import hd_root_key_from_seed

        short_seed = bytearray(32)
        with pytest.raises(ValueError, match="Seed must be 64 bytes"):
            hd_root_key_from_seed(short_seed)


class TestAccountManagerFromSecret:
    """Tests for AccountManager.from_secret method."""

    @pytest.fixture
    def algorand(self) -> AlgorandClient:
        return AlgorandClient.default_localnet()

    def test_from_secret_with_ed25519_seed(self, algorand: AlgorandClient) -> None:
        """Test from_secret with Ed25519 seed."""
        # Generate a random seed
        seed = os.urandom(32)

        class WrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                return bytearray(seed)

        account = algorand.account.from_secret(secret=WrappedSeed())

        # Verify account was created
        assert account.addr
        assert len(account.addr) == 58  # Algorand address length
        assert account.signer is not None

        # Verify we can get the signer
        signer = algorand.account.get_signer(account.addr)
        assert signer is not None

    def test_from_secret_with_hd_mnemonic(self, algorand: AlgorandClient) -> None:
        """Test from_secret with HD mnemonic."""

        class WrappedHdMnemonicImpl:
            def unwrap_hd_mnemonic(self) -> str:
                return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        account = algorand.account.from_secret(secret=WrappedHdMnemonicImpl())

        # Verify account was created
        assert account.addr
        assert len(account.addr) == 58
        assert account.signer is not None

    def test_from_secret_with_legacy_mnemonic(self, algorand: AlgorandClient) -> None:
        """Test from_secret with legacy mnemonic."""
        # Generate a random keypair and get its mnemonic
        keypair = pynacl_ed25519_generator()
        seed = keypair["ed25519_secret_key"][:32]
        mnemonic = mnemonic_from_seed(seed)

        class WrappedLegacyMnemonicImpl:
            def unwrap_legacy_mnemonic(self) -> str:
                return mnemonic

        account = algorand.account.from_secret(secret=WrappedLegacyMnemonicImpl())

        # Verify account was created
        assert account.addr
        assert len(account.addr) == 58
        assert account.signer is not None

        # Verify the address matches expected
        expected_address = algorand.account.from_mnemonic(mnemonic=mnemonic).addr
        assert account.addr == expected_address

    def test_from_secret_with_sender(self, algorand: AlgorandClient) -> None:
        """Test from_secret with sender address for rekeyed accounts."""
        # Generate a random seed
        seed = os.urandom(32)
        sender = "XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA"

        class WrappedSeed:
            def unwrap_ed25519_seed(self) -> bytearray:
                return bytearray(seed)

        account = algorand.account.from_secret(secret=WrappedSeed(), sender=sender)

        # Verify account was created with the sender address
        assert account.addr == sender
        assert account.signer is not None

    def test_from_mnemonic_deprecated(self, algorand: AlgorandClient) -> None:
        """Test that from_mnemonic raises deprecation warning."""
        # Generate a random keypair and get its mnemonic
        keypair = pynacl_ed25519_generator()
        seed = keypair["ed25519_secret_key"][:32]
        mnemonic = mnemonic_from_seed(seed)

        with pytest.warns(DeprecationWarning, match="from_mnemonic is deprecated"):
            account = algorand.account.from_mnemonic(mnemonic=mnemonic)

        # Account should still be created
        assert account.addr


class TestOptionalWrapMethods:
    """Tests that wrap methods are truly optional."""

    def test_ed25519_seed_without_wrap(self) -> None:
        """Ed25519 seed without wrap method should work."""
        seed = os.urandom(32)

        class WrappedSeedNoWrap:
            def unwrap_ed25519_seed(self) -> bytearray:
                return bytearray(seed)

            # Note: no wrap_ed25519_seed method

        wrapped = WrappedSeedNoWrap()
        signing_key = ed25519_signing_key_from_wrapped_secret(wrapped)

        message = b"test"
        signature = signing_key["raw_ed25519_signer"](message)
        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True

    def test_hd_extended_key_without_wrap(self) -> None:
        """HD extended key without wrap method should work."""
        from algokit_crypto import peikert_hd_wallet_generator

        wallet = peikert_hd_wallet_generator()
        account = wallet["account_generator"](0, 0)
        extended_key = bytearray(account["extended_private_key"])

        class WrappedHdKeyNoWrap:
            def unwrap_hd_extended_private_key(self) -> bytearray:
                return bytearray(extended_key)

            # Note: no wrap_hd_extended_private_key method

        wrapped = WrappedHdKeyNoWrap()
        signing_key = ed25519_signing_key_from_wrapped_secret(wrapped)

        message = b"test"
        signature = signing_key["raw_ed25519_signer"](message)
        assert ed25519_verifier(signature, message, signing_key["ed25519_pubkey"]) is True
