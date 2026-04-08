import pytest

import algokit_algod_client
import algokit_indexer_client

_ROUND = 24098947


def test_algod_tx_id_matches_indexer() -> None:
    algod_client = algokit_algod_client.AlgodClient(
        algokit_algod_client.ClientConfig(
            base_url="https://mainnet-api.algonode.cloud",
            token=None,
        )
    )
    indexer_client = algokit_indexer_client.IndexerClient(
        algokit_indexer_client.ClientConfig(
            base_url="https://mainnet-idx.algonode.cloud",
            token=None,
        )
    )

    algod_txns = algod_client.block(_ROUND).block.payset
    assert algod_txns is not None
    algod_txn = algod_txns[0].signed_transaction.signed_transaction.txn

    idx_txns = indexer_client.lookup_block(_ROUND).transactions
    assert idx_txns is not None
    idx_txn = idx_txns[0]

    assert algod_txn.tx_id() == idx_txn.id_


def test_algod_inner_tx_id() -> None:
    algod_client = algokit_algod_client.AlgodClient(
        algokit_algod_client.ClientConfig(
            base_url="https://mainnet-api.algonode.cloud",
            token=None,
        )
    )

    algod_txns = algod_client.block(35214367).block.payset
    assert algod_txns is not None
    apply_data = algod_txns[46].signed_transaction.apply_data
    assert apply_data is not None
    eval_data = apply_data.eval_delta
    assert eval_data is not None
    inner_txn = (eval_data.inner_txns or [])[0].signed_transaction.txn

    with pytest.raises(ValueError, match="Cannot compute transaction id without genesis hash"):
        assert inner_txn.tx_id()
