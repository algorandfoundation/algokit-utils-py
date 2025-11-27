import pytest

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ADDRESS

# Polytest Suite: GET v2_accounts_ADDRESS

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.account_information(TEST_ADDRESS)

    assert result is not None
    assert result.address == TEST_ADDRESS
    assert isinstance(result.amount, int)
    assert result.amount > 0
