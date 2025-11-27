import pytest

from algokit_algod_client import AlgodClient
from algokit_algod_client.config import ClientConfig

# Polytest Suite: GET v2_deltas_ROUND

# Polytest Group: Common Tests

# NOTE: This test uses live endpoints because PollyJS mock server doesn't properly
# handle msgpack responses for ledger state delta. See the TypeScript tests for
# similar approach: https://github.com/algorandfoundation/algokit-utils-ts


@pytest.mark.parametrize(
    ("base_url", "block_round"),
    [
        ("https://mainnet-api.4160.nodely.dev", 24098947),
        ("https://testnet-api.4160.nodely.dev", 24099447),
    ],
)
def test_basic_request_and_response_validation(base_url: str, block_round: int) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    config = ClientConfig(
        base_url=base_url,
        token=None,
    )
    algod_client = AlgodClient(config)

    result = algod_client.get_ledger_state_delta(round_=block_round)

    assert result is not None
    assert result.block is not None
    assert result.block.header.round == block_round
