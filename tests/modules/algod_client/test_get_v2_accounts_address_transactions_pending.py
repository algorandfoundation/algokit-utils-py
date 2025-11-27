import pytest

from algokit_algod_client import AlgodClient
from algokit_utils.algorand import AlgorandClient

# Polytest Suite: GET v2_accounts_ADDRESS_transactions_pending

# Polytest Group: Common Tests


# TODO: Fix msgpack response handling in PollyJS mock server
# This test is skipped because the mock server doesn't properly handle msgpack responses
# See TypeScript tests for similar skip: get_v_2_accounts_address_transactions_pending.test.ts
@pytest.mark.skip(reason="TODO: Fix msgpack response handling in PollyJS mock server")
@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient, algorand_localnet: AlgorandClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    dispenser = algorand_localnet.account.localnet_dispenser()

    result = algod_client.get_pending_transactions_by_address(dispenser.address)

    assert result is not None
    assert isinstance(result.total_transactions, int)
    # top_transactions may be empty if no pending transactions for this address
    assert result.top_transactions is not None
