import dataclasses
import os
from typing import Literal
from urllib import parse

from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

__all__ = [
    "AlgoClientConfig",
    "get_algod_client",
    "get_algonode_config",
    "get_default_localnet_config",
    "get_indexer_client",
    "get_kmd_client_from_algod_client",
    "is_localnet",
    "is_mainnet",
    "is_testnet",
    "AlgoClientConfigs",
    "get_kmd_client",
]


@dataclasses.dataclass
class AlgoClientConfig:
    """Connection details for connecting to an {py:class}`algosdk.v2client.algod.AlgodClient` or
    {py:class}`algosdk.v2client.indexer.IndexerClient`"""

    server: str
    """URL for the service e.g. `http://localhost:4001` or `https://testnet-api.algonode.cloud`"""
    token: str
    """API Token to authenticate with the service"""


@dataclasses.dataclass
class AlgoClientConfigs:
    algod_config: AlgoClientConfig
    indexer_config: AlgoClientConfig
    kmd_config: AlgoClientConfig | None


def get_default_localnet_config(config: Literal["algod", "indexer", "kmd"]) -> AlgoClientConfig:
    """Returns the client configuration to point to the default LocalNet"""
    port = {"algod": 4001, "indexer": 8980, "kmd": 4002}[config]
    return AlgoClientConfig(server=f"http://localhost:{port}", token="a" * 64)


def get_algonode_config(
    network: Literal["testnet", "mainnet"], config: Literal["algod", "indexer"], token: str
) -> AlgoClientConfig:
    client = "api" if config == "algod" else "idx"
    return AlgoClientConfig(
        server=f"https://{network}-{client}.algonode.cloud",
        token=token,
    )


def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
    """Returns an {py:class}`algosdk.v2client.algod.AlgodClient` from `config` or environment

    If no configuration provided will use environment variables `ALGOD_SERVER`, `ALGOD_PORT` and `ALGOD_TOKEN`"""
    config = config or _get_config_from_environment("ALGOD")
    headers = {"X-Algo-API-Token": config.token}
    return AlgodClient(config.token, config.server, headers)


def get_kmd_client(config: AlgoClientConfig | None = None) -> KMDClient:
    """Returns an {py:class}`algosdk.kmd.KMDClient` from `config` or environment

    If no configuration provided will use environment variables `KMD_SERVER`, `KMD_PORT` and `KMD_TOKEN`"""
    config = config or _get_config_from_environment("KMD")
    return KMDClient(config.token, config.server)  # type: ignore[no-untyped-call]


def get_indexer_client(config: AlgoClientConfig | None = None) -> IndexerClient:
    """Returns an {py:class}`algosdk.v2client.indexer.IndexerClient` from `config` or environment.

    If no configuration provided will use environment variables `INDEXER_SERVER`, `INDEXER_PORT` and `INDEXER_TOKEN`"""
    config = config or _get_config_from_environment("INDEXER")
    headers = {"X-Indexer-API-Token": config.token}
    return IndexerClient(config.token, config.server, headers)  # type: ignore[no-untyped-call]


def is_localnet(client: AlgodClient) -> bool:
    """Returns True if client genesis is `devnet-v1` or `sandnet-v1`"""
    params = client.suggested_params()
    return params.gen in ["devnet-v1", "sandnet-v1", "dockernet-v1"]


def is_mainnet(client: AlgodClient) -> bool:
    """Returns True if client genesis is `mainnet-v1`"""
    params = client.suggested_params()
    return params.gen in ["mainnet-v1.0", "mainnet-v1", "mainnet"]


def is_testnet(client: AlgodClient) -> bool:
    """Returns True if client genesis is `testnet-v1`"""
    params = client.suggested_params()
    return params.gen in ["testnet-v1.0", "testnet-v1", "testnet"]


def get_kmd_client_from_algod_client(client: AlgodClient) -> KMDClient:
    """Returns an {py:class}`algosdk.kmd.KMDClient` from supplied `client`

    Will use the same address as provided `client` but on port specified by `KMD_PORT` environment variable,
    or 4002 by default"""
    # We can only use Kmd on the LocalNet otherwise it's not exposed so this makes some assumptions
    # (e.g. same token and server as algod and port 4002 by default)
    port = os.getenv("KMD_PORT", "4002")
    server = _replace_kmd_port(client.algod_address, port)
    return KMDClient(client.algod_token, server)  # type: ignore[no-untyped-call]


def _replace_kmd_port(address: str, port: str) -> str:
    parsed_algod = parse.urlparse(address)
    kmd_host = parsed_algod.netloc.split(":", maxsplit=1)[0] + f":{port}"
    kmd_parsed = parsed_algod._replace(netloc=kmd_host)
    return parse.urlunparse(kmd_parsed)


def _get_config_from_environment(environment_prefix: str) -> AlgoClientConfig:
    server = os.getenv(f"{environment_prefix}_SERVER")
    if server is None:
        raise Exception(f"Server environment variable not set: {environment_prefix}_SERVER")
    port = os.getenv(f"{environment_prefix}_PORT")
    if port:
        parsed = parse.urlparse(server)
        server = parsed._replace(netloc=f"{parsed.hostname}:{port}").geturl()
    return AlgoClientConfig(server, os.getenv(f"{environment_prefix}_TOKEN", ""))
