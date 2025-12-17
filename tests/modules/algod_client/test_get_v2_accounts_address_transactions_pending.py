import pytest

from algokit_algod_client import AlgodClient

from tests.modules.conftest import TEST_ADDRESS

# Polytest Suite: GET v2_accounts_ADDRESS_transactions_pending

# Polytest Group: Common Tests


@pytest.mark.skip(reason="TODO: Re-enable once msgpack handling is fixed in mock server")
@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.pending_transactions_by_address(TEST_ADDRESS)

    assert result is not None
    assert isinstance(result.total_transactions, int)
    # top_transactions is None when there are no pending transactions (total_transactions == 0)
    # or a list when there are pending transactions
    if result.total_transactions > 0:
        assert result.top_transactions is not None
