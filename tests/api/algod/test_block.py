from __future__ import annotations

from algod_client import ClientConfig
from algod_client.client import AlgodClient


def test_block_endpoint() -> None:
    config = ClientConfig(
        base_url="https://testnet-api.4160.nodely.dev",
        token=None,
    )
    algod_client = AlgodClient(config)

    # Large block with state proof type txns on testnet (skip if not accessible)
    block_round = 24098947
    resp = algod_client.get_block(round_=block_round, header_only=False)

    assert resp.cert is not None
    assert resp.block.state_proof_tracking is not None
    assert resp.block.transactions is not None
    assert len(resp.block.transactions) > 0
