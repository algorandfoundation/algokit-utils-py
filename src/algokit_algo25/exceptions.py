"""Exceptions for mnemonic operations."""

__all__ = [
    "FAIL_TO_DECODE_MNEMONIC_ERROR_MSG",
    "NOT_IN_WORDS_LIST_ERROR_MSG",
    "InvalidMnemonicError",
    "InvalidSeedLengthError",
    "MnemonicError",
    "WordNotFoundError",
]

FAIL_TO_DECODE_MNEMONIC_ERROR_MSG = "failed to decode mnemonic"
NOT_IN_WORDS_LIST_ERROR_MSG = "the mnemonic contains a word that is not in the wordlist"


class MnemonicError(Exception):
    """Base exception for mnemonic operations."""


class InvalidMnemonicError(MnemonicError):
    """Invalid mnemonic format or checksum."""


class InvalidSeedLengthError(MnemonicError):
    """Seed length is not 32 bytes."""


class WordNotFoundError(InvalidMnemonicError):
    """Word not found in wordlist."""
