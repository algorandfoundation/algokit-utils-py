import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_indexer_client import IndexerClient

from tests.modules.conftest import TEST_ASSET_ID, DataclassSnapshotSerializer

# Polytest Suite: GET v2_assets_ASSET-ID

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(indexer_client: IndexerClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = indexer_client.lookup_asset_by_id(asset_id=TEST_ASSET_ID)

    assert result.asset is not None
    assert result.asset.id_ == TEST_ASSET_ID

    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
