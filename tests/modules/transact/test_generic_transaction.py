import pytest

from algokit_transact import (
    decode_transaction,
)

# Polytest Suite: Generic Transaction

# Polytest Group: Generic Transaction Tests


@pytest.mark.group_generic_transaction_tests
def test_malformed_bytes() -> None:
    """Ensure a helpful error message is thrown when attempting to decode malformed bytes"""
    with pytest.raises(ValueError, match="decoded msgpack is not a dict"):
        decode_transaction(b"\x01")


@pytest.mark.group_generic_transaction_tests
def test_encode_0_bytes() -> None:
    """Ensure a helpful error message is thrown when attempting to encode 0 bytes"""
    with pytest.raises(ValueError, match="^attempted to decode 0 bytes$"):
        decode_transaction(b"")
