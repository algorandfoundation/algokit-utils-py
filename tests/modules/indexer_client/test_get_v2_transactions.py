import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_indexer_client import IndexerClient

from tests.fixtures.schemas.indexer import TransactionsResponseSchema
from tests.modules.conftest import DataclassSnapshotSerializer, validate_with_schema

# Polytest Suite: GET v2_transactions

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(indexer_client: IndexerClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = indexer_client.search_for_transactions(limit=1)

    assert result.transactions is not None
    assert len(result.transactions) == 1

    validate_with_schema(result, TransactionsResponseSchema)
    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
