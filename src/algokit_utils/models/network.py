import dataclasses

__all__ = [
    "AlgoClientConfig",
    "AlgoClientConfigs",
]


@dataclasses.dataclass
class AlgoClientConfig:
    """Connection details for connecting to an {py:class}`algosdk.v2client.algod.AlgodClient` or
    {py:class}`algosdk.v2client.indexer.IndexerClient`"""

    server: str
    """URL for the service e.g. `http://localhost:4001` or `https://testnet-api.algonode.cloud`"""
    token: str | None = None
    """API Token to authenticate with the service"""
    port: str | int | None = None


@dataclasses.dataclass
class AlgoClientConfigs:
    algod_config: AlgoClientConfig
    indexer_config: AlgoClientConfig | None
    kmd_config: AlgoClientConfig | None
