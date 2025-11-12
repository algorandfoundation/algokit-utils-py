from algokit_algod_client import AlgodClient, ClientConfig


def test_ledger_state_delta_endpoint() -> None:
    config = ClientConfig(
        base_url="https://testnet-api.4160.nodely.dev",
        token=None,
    )
    algod_client = AlgodClient(config)

    # 1. Large block with state proof type txns on testnet (skip if not accessible)
    # 2. Block with global and local state deltas where keys can not be decoded as
    block_rounds = [24099447, 24099347]

    for block_round in block_rounds:
        resp = algod_client.get_ledger_state_delta(round_=block_round)

        assert resp.block.round == block_round
        assert resp.block.genesis_id == "testnet-v1.0"
        assert resp.accounts.accounts
        for account in resp.accounts.accounts:
            assert len(account.address) == 58
        assert resp.totals.online.money > 0
        assert resp.totals.offline.money >= 0
        assert resp.totals.not_participating.money >= 0

        # App resources (if any) should keep both IDs and decoded addresses.
        for resource in resp.accounts.app_resources or []:
            assert resource.app_id > 0
            assert len(resource.address) == 58
            if resource.state.local_state:
                # Local state deltas should track schema counts.
                assert resource.state.local_state.schema.num_byte_slices is not None

        # Creatables (if any) should expose creators and types.
        for creatable in (resp.creatables or {}).values():
            assert len(creatable.creator) == 58
            assert creatable.creatable_type in (0, 1)

        # TxIDs are keyed by raw digest bytes (32-byte values) with last-valid metadata.
        if resp.txids:
            for txid_bytes, tx_info in resp.txids.items():
                assert isinstance(txid_bytes, bytes)
                assert len(txid_bytes) == 32
                assert tx_info.last_valid >= block_round
