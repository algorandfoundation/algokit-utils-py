"""Tests for algokit_algo25 mnemonic functions."""

import os

import pytest

from algokit_algo25 import (
    FAIL_TO_DECODE_MNEMONIC_ERROR_MSG,
    NOT_IN_WORDS_LIST_ERROR_MSG,
    InvalidMnemonicError,
    InvalidSeedLengthError,
    WordNotFoundError,
    master_derivation_key_to_mnemonic,
    mnemonic_from_seed,
    mnemonic_to_master_derivation_key,
    secret_key_to_mnemonic,
    seed_from_mnemonic,
)


# Test vector: zero seed produces specific mnemonic
ZERO_SEED = bytes(32)
ZERO_SEED_MNEMONIC = (
    "abandon abandon abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon abandon abandon abandon invest"
)


class TestMnemonicFromSeed:
    def test_zero_seed(self) -> None:
        mnemonic = mnemonic_from_seed(ZERO_SEED)
        assert mnemonic == ZERO_SEED_MNEMONIC

    def test_returns_25_words(self) -> None:
        seed = os.urandom(32)
        mnemonic = mnemonic_from_seed(seed)
        words = mnemonic.split()
        assert len(words) == 25

    def test_invalid_seed_too_short(self) -> None:
        with pytest.raises(InvalidSeedLengthError):
            mnemonic_from_seed(bytes(31))

    def test_invalid_seed_too_long(self) -> None:
        with pytest.raises(InvalidSeedLengthError):
            mnemonic_from_seed(bytes(33))


class TestSeedFromMnemonic:
    def test_zero_seed_mnemonic(self) -> None:
        seed = seed_from_mnemonic(ZERO_SEED_MNEMONIC)
        assert seed == ZERO_SEED

    def test_case_insensitive(self) -> None:
        seed = seed_from_mnemonic(ZERO_SEED_MNEMONIC.upper())
        assert seed == ZERO_SEED

    def test_wrong_word_count(self) -> None:
        with pytest.raises(InvalidMnemonicError) as exc_info:
            seed_from_mnemonic("abandon abandon abandon")
        assert FAIL_TO_DECODE_MNEMONIC_ERROR_MSG in str(exc_info.value)

    def test_invalid_word(self) -> None:
        mnemonic = "invalidword " + " ".join(["abandon"] * 24)
        with pytest.raises(WordNotFoundError) as exc_info:
            seed_from_mnemonic(mnemonic)
        assert NOT_IN_WORDS_LIST_ERROR_MSG in str(exc_info.value)

    def test_wrong_checksum(self) -> None:
        # Replace checksum word with wrong word
        mnemonic = " ".join(["abandon"] * 25)  # wrong checksum
        with pytest.raises(InvalidMnemonicError) as exc_info:
            seed_from_mnemonic(mnemonic)
        assert FAIL_TO_DECODE_MNEMONIC_ERROR_MSG in str(exc_info.value)


class TestRoundtrip:
    def test_roundtrip_zero_seed(self) -> None:
        mnemonic = mnemonic_from_seed(ZERO_SEED)
        recovered = seed_from_mnemonic(mnemonic)
        assert recovered == ZERO_SEED

    def test_roundtrip_random_seeds(self) -> None:
        for _ in range(10):
            seed = os.urandom(32)
            mnemonic = mnemonic_from_seed(seed)
            recovered = seed_from_mnemonic(mnemonic)
            assert recovered == seed


class TestSecretKeyToMnemonic:
    def test_64_byte_key_uses_first_32_bytes(self) -> None:
        secret_key = ZERO_SEED + bytes(32)  # seed + dummy public key
        mnemonic = secret_key_to_mnemonic(secret_key)
        assert mnemonic == ZERO_SEED_MNEMONIC


class TestMasterDerivationKey:
    def test_to_mnemonic(self) -> None:
        mnemonic = master_derivation_key_to_mnemonic(ZERO_SEED)
        assert mnemonic == ZERO_SEED_MNEMONIC

    def test_from_mnemonic(self) -> None:
        key = mnemonic_to_master_derivation_key(ZERO_SEED_MNEMONIC)
        assert key == ZERO_SEED
