import pytest

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ROUND

# Polytest Suite: GET v2_blocks_ROUND_hash

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.get_block_hash(round_=TEST_ROUND)

    assert result is not None
    assert result.block_hash is not None
    assert isinstance(result.block_hash, str)
    assert len(result.block_hash) > 0
