import pytest

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ADDRESS, TEST_APP_ID

# Polytest Suite: GET v2_accounts_ADDRESS_applications_APPLICATION-ID

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.account_application_information(address=TEST_ADDRESS, application_id=TEST_APP_ID)

    assert result is not None
    assert result.app_local_state is not None or result.created_app is not None
