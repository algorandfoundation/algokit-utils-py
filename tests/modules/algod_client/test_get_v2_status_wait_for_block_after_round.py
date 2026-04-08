import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_algod_client import AlgodClient

from tests.fixtures.schemas.algod import NodeStatusResponseSchema
from tests.modules.conftest import TEST_ROUND, DataclassSnapshotSerializer, validate_with_schema

# Polytest Suite: GET v2_status_wait-for-block-after_ROUND

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.status_after_block(round_=TEST_ROUND)

    validate_with_schema(result, NodeStatusResponseSchema)
    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
