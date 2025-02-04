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
    """URL for the service e.g. `http://localhost` or `https://testnet-api.algonode.cloud`"""
    token: str | None = None
    """API Token to authenticate with the service e.g '4001' or '8980'"""
    port: str | int | None = None

    def full_url(self) -> str:
        """Returns the full URL for the service"""
        return f"{self.server.rstrip('/')}{f':{self.port}' if self.port else ''}"


@dataclasses.dataclass
class AlgoClientConfigs:
    algod_config: AlgoClientNetworkConfig
    indexer_config: AlgoClientNetworkConfig | None
    kmd_config: AlgoClientNetworkConfig | None
