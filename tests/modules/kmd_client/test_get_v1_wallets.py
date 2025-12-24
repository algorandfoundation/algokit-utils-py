import pytest

from algokit_kmd_client import KmdClient

# Polytest Suite: GET v1_wallets

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(localnet_kmd_client: KmdClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = localnet_kmd_client.list_wallets()

    assert result is not None
