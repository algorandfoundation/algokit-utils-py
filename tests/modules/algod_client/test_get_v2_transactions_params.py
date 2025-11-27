import pytest

from algokit_algod_client import AlgodClient

# Polytest Suite: GET v2_transactions_params

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.suggested_params()

    assert result is not None
    assert isinstance(result.genesis_id, str)
    assert result.genesis_id != ""
    assert isinstance(result.min_fee, int)
    assert result.min_fee > 0
