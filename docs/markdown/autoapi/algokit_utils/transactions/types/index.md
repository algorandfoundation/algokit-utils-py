# algokit_utils.transactions.types

## Attributes

| [`MethodCallParams`](#algokit_utils.transactions.types.MethodCallParams)   |    |
|----------------------------------------------------------------------------|----|
| [`TxnParams`](#algokit_utils.transactions.types.TxnParams)                 |    |

## Classes

| [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)                           |                                |
|--------------------------------------------------------------------------------------------------|--------------------------------|
| [`PaymentParams`](#algokit_utils.transactions.types.PaymentParams)                               |                                |
| [`AssetCreateParams`](#algokit_utils.transactions.types.AssetCreateParams)                       |                                |
| [`AssetConfigParams`](#algokit_utils.transactions.types.AssetConfigParams)                       |                                |
| [`AssetFreezeParams`](#algokit_utils.transactions.types.AssetFreezeParams)                       |                                |
| [`AssetDestroyParams`](#algokit_utils.transactions.types.AssetDestroyParams)                     |                                |
| [`OnlineKeyRegistrationParams`](#algokit_utils.transactions.types.OnlineKeyRegistrationParams)   |                                |
| [`OfflineKeyRegistrationParams`](#algokit_utils.transactions.types.OfflineKeyRegistrationParams) |                                |
| [`AssetTransferParams`](#algokit_utils.transactions.types.AssetTransferParams)                   |                                |
| [`AssetOptInParams`](#algokit_utils.transactions.types.AssetOptInParams)                         |                                |
| [`AssetOptOutParams`](#algokit_utils.transactions.types.AssetOptOutParams)                       |                                |
| [`AppCallParams`](#algokit_utils.transactions.types.AppCallParams)                               |                                |
| [`AppCreateSchema`](#algokit_utils.transactions.types.AppCreateSchema)                           | dict() -> new empty dictionary |
| [`AppCreateParams`](#algokit_utils.transactions.types.AppCreateParams)                           |                                |
| [`AppUpdateParams`](#algokit_utils.transactions.types.AppUpdateParams)                           |                                |
| [`AppDeleteParams`](#algokit_utils.transactions.types.AppDeleteParams)                           |                                |
| [`AppMethodCallParams`](#algokit_utils.transactions.types.AppMethodCallParams)                   |                                |
| [`AppCallMethodCallParams`](#algokit_utils.transactions.types.AppCallMethodCallParams)           |                                |
| [`AppCreateMethodCallParams`](#algokit_utils.transactions.types.AppCreateMethodCallParams)       |                                |
| [`AppUpdateMethodCallParams`](#algokit_utils.transactions.types.AppUpdateMethodCallParams)       |                                |
| [`AppDeleteMethodCallParams`](#algokit_utils.transactions.types.AppDeleteMethodCallParams)       |                                |

## Module Contents

### *class* algokit_utils.transactions.types.CommonTxnParams

#### sender *: str*

#### signer *: algokit_transact.signer.TransactionSigner | algokit_transact.signer.AddressWithTransactionSigner | None* *= None*

#### rekey_to *: str | None* *= None*

#### note *: bytes | None* *= None*

#### lease *: bytes | None* *= None*

#### static_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### extra_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### max_fee *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount) | None* *= None*

#### validity_window *: int | None* *= None*

#### first_valid_round *: int | None* *= None*

#### last_valid_round *: int | None* *= None*

### *class* algokit_utils.transactions.types.PaymentParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### receiver *: str*

#### amount *: [algokit_utils.models.amount.AlgoAmount](../../models/amount/index.md#algokit_utils.models.amount.AlgoAmount)*

#### close_remainder_to *: str | None* *= None*

### *class* algokit_utils.transactions.types.AssetCreateParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### total *: int*

#### asset_name *: str | None* *= None*

#### unit_name *: str | None* *= None*

#### url *: str | None* *= None*

#### decimals *: int | None* *= None*

#### default_frozen *: bool | None* *= None*

#### manager *: str | None* *= None*

#### reserve *: str | None* *= None*

#### freeze *: str | None* *= None*

#### clawback *: str | None* *= None*

#### metadata_hash *: bytes | None* *= None*

### *class* algokit_utils.transactions.types.AssetConfigParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### asset_id *: int*

#### manager *: str | None* *= None*

#### reserve *: str | None* *= None*

#### freeze *: str | None* *= None*

#### clawback *: str | None* *= None*

### *class* algokit_utils.transactions.types.AssetFreezeParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### asset_id *: int*

#### account *: str*

#### frozen *: bool*

### *class* algokit_utils.transactions.types.AssetDestroyParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### asset_id *: int*

### *class* algokit_utils.transactions.types.OnlineKeyRegistrationParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### vote_key *: str*

#### selection_key *: str*

#### state_proof_key *: bytes | None* *= None*

#### vote_first *: int* *= 0*

#### vote_last *: int* *= 0*

#### vote_key_dilution *: int* *= 0*

#### nonparticipation *: bool | None* *= None*

### *class* algokit_utils.transactions.types.OfflineKeyRegistrationParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### prevent_account_from_ever_participating_again *: bool* *= True*

### *class* algokit_utils.transactions.types.AssetTransferParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### asset_id *: int*

#### amount *: int*

#### receiver *: str*

#### close_asset_to *: str | None* *= None*

#### clawback_target *: str | None* *= None*

### *class* algokit_utils.transactions.types.AssetOptInParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### asset_id *: int*

### *class* algokit_utils.transactions.types.AssetOptOutParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### asset_id *: int*

#### creator *: str*

### *class* algokit_utils.transactions.types.AppCallParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### app_id *: int*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[algokit_utils.models.state.BoxReference | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### on_complete *: algokit_transact.OnApplicationComplete | None* *= None*

### *class* algokit_utils.transactions.types.AppCreateSchema

Bases: `TypedDict`

dict() -> new empty dictionary
dict(mapping) -> new dictionary initialized from a mapping object’s

> (key, value) pairs

dict(iterable) -> new dictionary initialized as if via:
: d = {}
  for k, v in iterable:
  <br/>
  > d[k] = v

dict(

```
**
```

kwargs) -> new dictionary initialized with the name=value pairs
: in the keyword argument list.  For example:  dict(one=1, two=2)

#### global_ints *: int*

#### global_byte_slices *: int*

#### local_ints *: int*

#### local_byte_slices *: int*

### *class* algokit_utils.transactions.types.AppCreateParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### schema *: [AppCreateSchema](#algokit_utils.transactions.types.AppCreateSchema) | None* *= None*

#### on_complete *: algokit_transact.OnApplicationComplete | None* *= None*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[algokit_utils.models.state.BoxReference | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### extra_program_pages *: int | None* *= None*

### *class* algokit_utils.transactions.types.AppUpdateParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### app_id *: int*

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[algokit_utils.models.state.BoxReference | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### on_complete *: algokit_transact.OnApplicationComplete*

### *class* algokit_utils.transactions.types.AppDeleteParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### app_id *: int*

#### args *: list[bytes] | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[algokit_utils.models.state.BoxReference | algokit_utils.models.state.BoxIdentifier] | None* *= None*

#### on_complete *: algokit_transact.OnApplicationComplete | None* *= None*

### *class* algokit_utils.transactions.types.AppMethodCallParams

Bases: [`CommonTxnParams`](#algokit_utils.transactions.types.CommonTxnParams)

#### app_id *: int*

#### method *: algokit_abi.arc56.Method*

#### args *: list[bytes] | None* *= None*

#### on_complete *: algokit_transact.OnApplicationComplete | None* *= None*

#### account_references *: list[str] | None* *= None*

#### app_references *: list[int] | None* *= None*

#### asset_references *: list[int] | None* *= None*

#### box_references *: list[algokit_utils.models.state.BoxReference | algokit_utils.models.state.BoxIdentifier] | None* *= None*

### *class* algokit_utils.transactions.types.AppCallMethodCallParams

Bases: `_BaseAppMethodCall`

#### app_id *: int*

#### on_complete *: algokit_transact.OnApplicationComplete | None* *= None*

### *class* algokit_utils.transactions.types.AppCreateMethodCallParams

Bases: `_BaseAppMethodCall`

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### schema *: [AppCreateSchema](#algokit_utils.transactions.types.AppCreateSchema) | None* *= None*

#### on_complete *: algokit_transact.OnApplicationComplete | None* *= None*

### *class* algokit_utils.transactions.types.AppUpdateMethodCallParams

Bases: `_BaseAppMethodCall`

#### app_id *: int*

#### approval_program *: str | bytes*

#### clear_state_program *: str | bytes*

#### on_complete *: algokit_transact.OnApplicationComplete*

### *class* algokit_utils.transactions.types.AppDeleteMethodCallParams

Bases: `_BaseAppMethodCall`

#### app_id *: int*

#### on_complete *: algokit_transact.OnApplicationComplete*

### algokit_utils.transactions.types.MethodCallParams

### algokit_utils.transactions.types.TxnParams
