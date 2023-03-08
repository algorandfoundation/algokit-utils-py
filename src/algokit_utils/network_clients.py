import dataclasses
import os
import re

from algosdk.kmd import KMDClient
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient


@dataclasses.dataclass
class AlgoClientConfig:
    server: str
    token: str | None = None


def _get_config_from_environment(environment_prefix: str) -> AlgoClientConfig:
    server = os.getenv(f"{environment_prefix}_SERVER")
    if server is None:
        raise Exception(f"Server environment variable not set: {environment_prefix}_SERVER")
    return AlgoClientConfig(server, os.getenv(f"{environment_prefix}_TOKEN"))


def get_algod_client(config: AlgoClientConfig | None = None) -> AlgodClient:
    # TODO: alternate headers etc.
    config = config or _get_config_from_environment("ALGOD")
    return AlgodClient(config.token, config.server)  # type: ignore[no-untyped-call]


def get_indexer_client(config: AlgoClientConfig | None = None) -> IndexerClient:
    config = config or _get_config_from_environment("INDEXER")
    return IndexerClient(config.token, config.server)  # type: ignore[no-untyped-call]


def is_sandbox(client: AlgodClient) -> bool:
    params = client.suggested_params()  # type: ignore[no-untyped-call]
    return params.gen in ["devnet-v1", "sandnet-v1"]


def _replace_kmd_port(address: str, port: str) -> str:
    # TODO: parse this properly

    match = re.search(r"(:[0-9]+/?)$", address)
    if match:
        address = address[: -len(match.group(1))]
    return f"{address}:{port}"


def get_kmd_client_from_algod_client(client: AlgodClient) -> KMDClient:
    # We can only use Kmd on the Sandbox otherwise it's not exposed so this makes some assumptions
    # (e.g. same token and server as algod and port 4002 by default)
    port = os.getenv("KMD_PORT", "4002")
    server = _replace_kmd_port(client.algod_address, port)
    return KMDClient(client.algod_token, server)  # type: ignore[no-untyped-call]
