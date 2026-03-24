import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_indexer_client import IndexerClient

from tests.fixtures.schemas.indexer import ApplicationLogsResponseSchema
from tests.modules.conftest import TEST_APP_ID, DataclassSnapshotSerializer, validate_with_schema

# Polytest Suite: GET v2_applications_APPLICATION-ID_logs

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(indexer_client: IndexerClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = indexer_client.lookup_application_logs_by_id(TEST_APP_ID)

    validate_with_schema(result, ApplicationLogsResponseSchema)
    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
