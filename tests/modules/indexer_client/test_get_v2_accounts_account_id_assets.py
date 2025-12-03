import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_indexer_client import IndexerClient

from tests.modules.conftest import TEST_ADDRESS, DataclassSnapshotSerializer

# Polytest Suite: GET v2_accounts_ACCOUNT-ID_assets

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(indexer_client: IndexerClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = indexer_client.lookup_account_assets(TEST_ADDRESS)

    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
