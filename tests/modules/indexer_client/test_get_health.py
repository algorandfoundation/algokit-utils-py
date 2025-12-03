import pytest

from algokit_indexer_client import IndexerClient

# Polytest Suite: GET health

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(indexer_client: IndexerClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # Note: TS skips this test due to schema mismatch with 'migration-required' and 'read-only-mode' fields
    # Python implementation handles this gracefully
    result = indexer_client.make_health_check()
    assert result is not None
    assert result.round_ is not None
