import pytest

from algokit_algod_client import AlgodClient

# Polytest Suite: GET health

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # health_check returns None on success (200 OK with empty body)
    result = algod_client.health_check()
    assert result is None
