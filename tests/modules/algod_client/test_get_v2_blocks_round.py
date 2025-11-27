import pytest

from algokit_algod_client import AlgodClient, ClientConfig

# Polytest Suite: GET v2_blocks_ROUND

# Polytest Group: Common Tests

# Note: This test uses a live endpoint because the mock server doesn't properly
# handle msgpack responses. See TS test for similar approach.
LIVE_ALGOD_URL = "https://mainnet-api.4160.nodely.dev"


@pytest.mark.group_common_tests
def test_basic_request_and_response_validation() -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # Use live endpoint like TS tests do (mock server has issues with msgpack)
    config = ClientConfig(base_url=LIVE_ALGOD_URL)
    client = AlgodClient(config)

    # Test same rounds as TS tests
    result = client.get_block(round_=24098947)
    assert result is not None
    assert result.block is not None
    assert result.block.header is not None
    assert result.block.header.round == 24098947

    result2 = client.get_block(round_=55240407)
    assert result2 is not None
    assert result2.block is not None
    assert result2.block.header is not None
    assert result2.block.header.round == 55240407

    result3 = client.get_block(round_=35600004)  # stpf in block
    assert result3 is not None
    assert result3.block is not None
    assert result3.block.header is not None
    assert result3.block.header.round == 35600004
