import pytest

from algokit_algod_client import AlgodClient, ClientConfig


@pytest.mark.parametrize(
    ("base_url", "block_rounds", "genesis_id"),
    [
        ("https://mainnet-api.4160.nodely.dev", [24098947, 55240407], "mainnet-v1.0"),
        ("https://testnet-api.4160.nodely.dev", [24099447, 24099347], "testnet-v1.0"),
    ],
)
def test_ledger_state_delta_endpoint(base_url: str, block_rounds: list[int], genesis_id: str) -> None:
    config = ClientConfig(
        base_url=base_url,
        token=None,
    )
    algod_client = AlgodClient(config)

    for block_round in block_rounds:
        resp = algod_client.get_ledger_state_delta(round_=block_round)

        assert resp.block.round == block_round
        assert resp.block.genesis_id == genesis_id

        # Blocks may have no account changes
        for account in resp.accounts.accounts:
            assert len(account.address) == 58  # base32 + checksum

        # Totals can be zero if no changes
        assert resp.totals.online.money >= 0
        assert resp.totals.offline.money >= 0
        assert resp.totals.not_participating.money >= 0

        for resource in resp.accounts.app_resources or []:
            assert resource.app_id > 0
            assert len(resource.address) == 58
            if resource.state.local_state:
                schema = resource.state.local_state.schema
                assert schema.num_uints is not None or schema.num_byte_slices is not None

        for creatable in (resp.creatables or {}).values():
            assert len(creatable.creator) == 58
            assert creatable.creatable_type in (0, 1)

        if resp.tx_ids:
            for txid_bytes, tx_info in resp.tx_ids.items():
                assert isinstance(txid_bytes, bytes)
                assert len(txid_bytes) == 32
                assert tx_info.last_valid >= block_round
