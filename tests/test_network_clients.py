from algokit_utils import (
    get_algod_client,
    get_algonode_config,
    get_default_localnet_config,
    get_indexer_client,
    get_purestake_config,
)

DEFAULT_TOKEN = "a" * 64


def test_localnet_algod() -> None:
    algod_client = get_algod_client(get_default_localnet_config("algod"))
    health_response = algod_client.health()
    assert health_response is None


def test_localnet_indexer() -> None:
    indexer_client = get_indexer_client(get_default_localnet_config("indexer"))
    health_response = indexer_client.health()  # type: ignore[no-untyped-call]
    assert isinstance(health_response, dict)


def test_purestake_headers() -> None:
    algod_client = get_algod_client(get_purestake_config("testnet", "algod", DEFAULT_TOKEN))
    indexer_client = get_indexer_client(get_purestake_config("testnet", "indexer", DEFAULT_TOKEN))

    assert algod_client.headers == {"X-API-Key": DEFAULT_TOKEN}
    assert indexer_client.headers == {"X-API-Key": DEFAULT_TOKEN}


def test_cloudnode_algod_headers() -> None:
    algod_client = get_algod_client(get_algonode_config("testnet", "algod", DEFAULT_TOKEN))

    assert algod_client.headers == {"X-Algo-API-Token": DEFAULT_TOKEN}


def test_cloudnode_indexer_headers() -> None:
    indexer_client = get_indexer_client(get_algonode_config("testnet", "indexer", DEFAULT_TOKEN))

    assert indexer_client.headers == {"X-Indexer-API-Token": DEFAULT_TOKEN}
