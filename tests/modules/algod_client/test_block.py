from algokit_algod_client import AlgodClient, ClientConfig


def test_block_endpoint() -> None:
    config = ClientConfig(
        base_url="https://testnet-api.4160.nodely.dev",
        token=None,
    )
    algod_client = AlgodClient(config)

    # 1. Large block with state proof type txns on testnet (skip if not accessible)
    # 2. Block with global and local state deltas where keys can not be decoded as
    block_rounds = [24099447, 24099347]

    for block_round in block_rounds:
        resp = algod_client.get_block(round_=block_round, header_only=False)

        assert resp.block.state_proof_tracking is not None
        assert resp.block.transactions is not None
        assert len(resp.block.transactions) > 0
