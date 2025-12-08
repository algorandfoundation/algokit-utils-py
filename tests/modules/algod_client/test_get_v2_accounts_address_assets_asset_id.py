import pytest
from syrupy.assertion import SnapshotAssertion

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ADDRESS, TEST_ASSET_ID, DataclassSnapshotSerializer

# Polytest Suite: GET v2_accounts_ADDRESS_assets_ASSET-ID

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient, snapshot_json: SnapshotAssertion) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.account_asset_information(TEST_ADDRESS, TEST_ASSET_ID)

    assert DataclassSnapshotSerializer.serialize(result) == snapshot_json
