import pytest

from algokit_algod_client import AlgodClient

# Polytest Suite: GET genesis

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.get_genesis()

    assert result is not None
    assert isinstance(result.network, str)
    assert result.network != ""
