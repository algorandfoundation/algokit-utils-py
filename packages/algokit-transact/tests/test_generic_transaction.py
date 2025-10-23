import pytest

from algokit_transact import decode_transaction

from .common import get_test_vector


def test_malformed_bytes():
    vector = get_test_vector("simplePayment")
    bad_bytes = vector.unsigned_bytes[13:37]
    with pytest.raises(ValueError):
        decode_transaction(bad_bytes)


def test_encode_0_bytes():
    with pytest.raises(ValueError, match="^attempted to decode 0 bytes$"):
        decode_transaction(b"")
