import pytest

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ROUND

# Polytest Suite: GET v2_status_wait-for-block-after_ROUND

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.wait_for_block(round_=TEST_ROUND)

    assert result is not None
    assert isinstance(result.last_round, int)
    assert result.last_round >= TEST_ROUND
