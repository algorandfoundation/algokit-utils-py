import dataclasses
import os
import warnings
from urllib import parse

from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

__all__ = [
    "AlgoClientConfig",
    "get_algod_client",
    "get_indexer_client",
    "get_kmd_client_from_algod_client",
    "is_localnet",
    "is_sandbox",
]

_PURE_STAKE_HOST = "purestake.io"


@dataclasses.dataclass
class AlgoClientConfig:
    """Connection details for connecting to an {py:class}`algosdk.v2client.algod.AlgodClient` or
    {py:class}`algosdk.v2client.indexer.IndexerClient`"""

    server: str
    """URL for the service e.g. `http://localhost:4001` or `https://testnet-api.algonode.cloud`"""
    token: str
    """API Token to authenticate with the service"""


def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
    """Returns an {py:class}`algosdk.v2client.algod.AlgodClient` from `config` or environment

    If no configuration provided will use environment variables `ALGOD_SERVER`, `ALGOD_PORT` and `ALGOD_TOKEN`"""
    config = config or _get_config_from_environment("ALGOD")
    headers = _get_headers(config)
    return AlgodClient(config.token, config.server, headers)


def get_indexer_client(config: AlgoClientConfig | None = None) -> IndexerClient:
    """Returns an {py:class}`algosdk.v2client.indexer.IndexerClient` from `config` or environment.

    If no configuration provided will use environment variables `INDEXER_SERVER`, `INDEXER_PORT` and `INDEXER_TOKEN`"""
    config = config or _get_config_from_environment("INDEXER")
    headers = _get_headers(config)
    return IndexerClient(config.token, config.server, headers)  # type: ignore[no-untyped-call]


def is_localnet(client: AlgodClient) -> bool:
    """Returns True if client genesis is `devnet-v1` or `sandnet-v1`"""
    params = client.suggested_params()
    return params.gen in ["devnet-v1", "sandnet-v1"]


def is_sandbox(client: AlgodClient) -> bool:
    warnings.warn("is_sandbox is deprecated, please use is_localnet instead", DeprecationWarning, stacklevel=2)
    return is_localnet(client)


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
        server = server.rstrip("/")
        server = f"{server}:{port}"
    return AlgoClientConfig(server, os.getenv(f"{environment_prefix}_TOKEN", ""))


def _is_pure_stake_url(url: str) -> bool:
    parsed = parse.urlparse(url)
    host = parsed.netloc.split(":")[0].lower()
    return host.endswith(_PURE_STAKE_HOST)


def _get_headers(config: AlgoClientConfig) -> dict[str, str] | None:
    return {"X-API-TOKEN": config.token} if _is_pure_stake_url(config.server) else None
