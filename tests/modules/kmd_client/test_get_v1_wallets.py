import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_kmd_client import KmdClient

from tests.modules.conftest import DataclassSnapshotSerializer

# Polytest Suite: GET v1_wallets

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(kmd_client: KmdClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = kmd_client.list_wallets()

    assert result.wallets is not None

    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
