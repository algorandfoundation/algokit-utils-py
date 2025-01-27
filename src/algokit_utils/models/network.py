import dataclasses

__all__ = [
    "AlgoClientConfigs",
    "AlgoClientNetworkConfig",
]


@dataclasses.dataclass
class AlgoClientNetworkConfig:
    """Connection details for connecting to an {py:class}`algosdk.v2client.algod.AlgodClient` or
    {py:class}`algosdk.v2client.indexer.IndexerClient`"""

    server: str
    """URL for the service e.g. `http://localhost:4001` or `https://testnet-api.algonode.cloud`"""
    token: str | None = None
    """API Token to authenticate with the service"""
    port: str | int | None = None


@dataclasses.dataclass
class AlgoClientConfigs:
    algod_config: AlgoClientNetworkConfig
    indexer_config: AlgoClientNetworkConfig | None
    kmd_config: AlgoClientNetworkConfig | None
