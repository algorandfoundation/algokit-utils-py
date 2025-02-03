# algokit_utils.models.network

## Classes

| [`AlgoClientNetworkConfig`](#algokit_utils.models.network.AlgoClientNetworkConfig)   | Connection details for connecting to an {py:class}\`algosdk.v2client.algod.AlgodClient\` or   |
|--------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [`AlgoClientConfigs`](#algokit_utils.models.network.AlgoClientConfigs)               |                                                                                               |

## Module Contents

### *class* algokit_utils.models.network.AlgoClientNetworkConfig

Connection details for connecting to an {py:class}\`algosdk.v2client.algod.AlgodClient\` or
{py:class}\`algosdk.v2client.indexer.IndexerClient\`

#### server *: str*

URL for the service e.g. http://localhost or https://testnet-api.algonode.cloud

#### token *: str | None* *= None*

API Token to authenticate with the service e.g ‘4001’ or ‘8980’

#### port *: str | int | None* *= None*

### *class* algokit_utils.models.network.AlgoClientConfigs

#### algod_config *: [AlgoClientNetworkConfig](#algokit_utils.models.network.AlgoClientNetworkConfig)*

#### indexer_config *: [AlgoClientNetworkConfig](#algokit_utils.models.network.AlgoClientNetworkConfig) | None*

#### kmd_config *: [AlgoClientNetworkConfig](#algokit_utils.models.network.AlgoClientNetworkConfig) | None*
