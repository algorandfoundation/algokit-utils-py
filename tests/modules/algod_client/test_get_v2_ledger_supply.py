import pytest

from algokit_algod_client import AlgodClient

# Polytest Suite: GET v2_ledger_supply

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation(algod_client: AlgodClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = algod_client.get_supply()

    assert result is not None
    assert isinstance(result.current_round, int)
    assert isinstance(result.online_money, int)
    assert isinstance(result.total_money, int)
    assert result.total_money > 0
