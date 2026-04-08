import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_indexer_client import IndexerClient

from tests.fixtures.schemas.indexer import TransactionsResponseSchema
from tests.modules.conftest import TEST_ASSET_ID, DataclassSnapshotSerializer, validate_with_schema

# Polytest Suite: GET v2_assets_ASSET-ID_transactions

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(indexer_client: IndexerClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # No limit parameter to match HAR recording
    result = indexer_client.lookup_asset_transactions(asset_id=TEST_ASSET_ID)

    assert result.transactions is not None

    validate_with_schema(result, TransactionsResponseSchema)
    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
