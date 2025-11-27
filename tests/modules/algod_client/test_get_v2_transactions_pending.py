import pytest

from algokit_algod_client import AlgodClient

# Polytest Suite: GET v2_transactions_pending

# Polytest Group: Common Tests


# TODO: Fix msgpack response handling in PollyJS mock server
# This test is skipped because the mock server doesn't properly handle msgpack responses
# See TypeScript tests for similar skip: get_v_2_transactions_pending.test.ts
@pytest.mark.skip(reason="TODO: Fix msgpack response handling in PollyJS mock server")
@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.get_pending_transactions()

    assert result is not None
    assert isinstance(result.total_transactions, int)
    # top_transactions may be empty if no pending transactions
    assert result.top_transactions is not None
