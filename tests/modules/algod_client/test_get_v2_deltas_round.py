import pytest

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ROUND

# Polytest Suite: GET v2_deltas_ROUND

# Polytest Group: Common Tests


@pytest.mark.skip(reason="TODO: Re-enable once msgpack handling is fixed in mock server")
@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.ledger_state_delta(round_=TEST_ROUND)

    assert result is not None
    assert result.block is not None
    assert result.block.header.round == TEST_ROUND
