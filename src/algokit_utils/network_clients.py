import dataclasses
import os
from urllib import parse

from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

_PURE_STAKE_HOST = "purestake.io"


@dataclasses.dataclass
class AlgoClientConfig:
    server: str
    token: str = ""


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


def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
    config = config or _get_config_from_environment("ALGOD")
    headers = _get_headers(config)
    return AlgodClient(config.token, config.server, headers)


def get_indexer_client(config: AlgoClientConfig | None = None) -> IndexerClient:
    config = config or _get_config_from_environment("INDEXER")
    headers = _get_headers(config)
    return IndexerClient(config.token, config.server, headers)  # type: ignore[no-untyped-call]


def is_sandbox(client: AlgodClient) -> bool:
    params = client.suggested_params()
    return params.gen in ["devnet-v1", "sandnet-v1"]


def _replace_kmd_port(address: str, port: str) -> str:
    parsed_algod = parse.urlparse(address)
    kmd_host = parsed_algod.netloc.split(":", maxsplit=1)[0] + f":{port}"
    kmd_parsed = parsed_algod._replace(netloc=kmd_host)
    return parse.urlunparse(kmd_parsed)


def get_kmd_client_from_algod_client(client: AlgodClient) -> KMDClient:
    # We can only use Kmd on the Sandbox otherwise it's not exposed so this makes some assumptions
    # (e.g. same token and server as algod and port 4002 by default)
    port = os.getenv("KMD_PORT", "4002")
    server = _replace_kmd_port(client.algod_address, port)
    return KMDClient(client.algod_token, server)  # type: ignore[no-untyped-call]
