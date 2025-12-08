import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_indexer_client import IndexerClient

from tests.modules.conftest import DataclassSnapshotSerializer

# Polytest Suite: GET v2_block-headers

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(indexer_client: IndexerClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # Only limit=1 to match HAR recording (no min_round/max_round)
    result = indexer_client.search_for_block_headers(limit=1)

    assert result.blocks is not None
    assert len(result.blocks) == 1

    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
