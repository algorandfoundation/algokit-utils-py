import pytest

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ASSET_ID

# Polytest Suite: GET v2_assets_ASSET-ID

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.get_asset_by_id(asset_id=TEST_ASSET_ID)

    assert result is not None
    assert result.id_ == TEST_ASSET_ID
    assert result.params is not None
