# algokit_utils.applications.app_client.AppClientParams

#### *class* algokit_utils.applications.app_client.AppClientParams

Full parameters for creating an app client

#### app_spec *: [algokit_utils.applications.app_spec.arc56.Arc56Contract](../app_spec/arc56/Arc56Contract.md#algokit_utils.applications.app_spec.arc56.Arc56Contract) | [algokit_utils.applications.app_spec.arc32.Arc32Contract](../app_spec/arc32/Arc32Contract.md#algokit_utils.applications.app_spec.arc32.Arc32Contract) | str*

The application specification

#### algorand *: [algokit_utils.algorand.AlgorandClient](../../algorand/AlgorandClient.md#algokit_utils.algorand.AlgorandClient)*

The Algorand client

#### app_id *: int*

The application ID

#### app_name *: str | None* *= None*

The application name

#### default_sender *: str | None* *= None*

The default sender address

#### default_signer *: algosdk.atomic_transaction_composer.TransactionSigner | None* *= None*

The default transaction signer

#### approval_source_map *: algosdk.source_map.SourceMap | None* *= None*

The approval source map

#### clear_source_map *: algosdk.source_map.SourceMap | None* *= None*

The clear source map
