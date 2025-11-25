# algokit_utils.applications.abi

## Attributes

| [`ABIValue`](#algokit_utils.applications.abi.ABIValue)                         |    |
|--------------------------------------------------------------------------------|----|
| [`ABIStruct`](#algokit_utils.applications.abi.ABIStruct)                       |    |
| [`Arc56ReturnValueType`](#algokit_utils.applications.abi.Arc56ReturnValueType) |    |
| [`ABIType`](#algokit_utils.applications.abi.ABIType)                           |    |
| [`ABIArgumentType`](#algokit_utils.applications.abi.ABIArgumentType)           |    |

## Classes

| [`ABIReturn`](#algokit_utils.applications.abi.ABIReturn)     | Represents the return value from an ABI method call.                 |
|--------------------------------------------------------------|----------------------------------------------------------------------|
| [`ABIResult`](#algokit_utils.applications.abi.ABIResult)     | Deprecated wrapper that previously carried tx context plus ABI data. |
| [`BoxABIValue`](#algokit_utils.applications.abi.BoxABIValue) | Represents an ABI value stored in a box.                             |

## Functions

| [`extract_abi_return_from_logs`](#algokit_utils.applications.abi.extract_abi_return_from_logs)(→ ABIReturn)   | Decode ABI return value from a transaction confirmation log.   |
|---------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| [`parse_abi_method_result`](#algokit_utils.applications.abi.parse_abi_method_result)(→ ABIResult)             | Deprecated: use extract_abi_return_from_logs instead.          |
| [`get_arc56_value`](#algokit_utils.applications.abi.get_arc56_value)(→ Arc56ReturnValueType)                  | Deprecated: use ABIReturn.value instead.                       |
| [`get_abi_encoded_value`](#algokit_utils.applications.abi.get_abi_encoded_value)(→ bytes)                     | Encodes a value according to its ABI type.                     |
| [`get_abi_decoded_value`](#algokit_utils.applications.abi.get_abi_decoded_value)(→ ABIValue)                  | Decodes a value according to its ABI type.                     |
| [`prepare_value_for_atc`](#algokit_utils.applications.abi.prepare_value_for_atc)(→ Any)                       | Recursively converts any structs present in value to a tuple,  |

## Module Contents

### *type* algokit_utils.applications.abi.ABIValue *= bool | int | str | bytes | bytearray | list['ABIValue'] | tuple['ABIValue'] | dict[str, 'ABIValue']*

### *type* algokit_utils.applications.abi.ABIStruct *= dict[str, list[dict[str, 'ABIValue']]]*

### *type* algokit_utils.applications.abi.Arc56ReturnValueType *= ABIValue | ABIStruct | None*

### *type* algokit_utils.applications.abi.ABIType *= algokit_abi.ABIType*

### *type* algokit_utils.applications.abi.ABIArgumentType *= algokit_abi.ABIType | arc56.TransactionType | arc56.ReferenceType*

### *class* algokit_utils.applications.abi.ABIReturn(\*, method: Arc56Method | None, raw_value: bytes = b'', value: ABIValue | None = None, decode_error: Exception | None = None, tx_info: ConfirmationResponse | None = None)

Represents the return value from an ABI method call.

Aligns with the Rust model: always carries the method, raw bytes, decoded value (if available),
and any decode error. Transaction context should live on the send result, not here.

#### method *: Arc56Method | None*

#### raw_value *: bytes*

#### value *: ABIValue | None*

#### decode_error *: Exception | None*

#### *property* is_success *: bool*

Returns True if the ABI call was decoded successfully.

#### *property* tx_info *: ConfirmationResponse | None*

Deprecated: transaction info now lives on the send result.

#### get_arc56_value(method: algokit_abi.arc56.Method, structs: dict[str, object] | None = None) → Arc56ReturnValueType

Deprecated: use value directly.

### *class* algokit_utils.applications.abi.ABIResult(\*, tx_id: str | None = None, raw_value: bytes = b'', value: ABIValue | None = None, decode_error: Exception | None = None, tx_info: ConfirmationResponse | None = None, method: Arc56Method | None = None)

Bases: [`ABIReturn`](#algokit_utils.applications.abi.ABIReturn)

Deprecated wrapper that previously carried tx context plus ABI data.

#### tx_id *: str | None* *= None*

#### *classmethod* from_abireturn(abi_return: [ABIReturn](#algokit_utils.applications.abi.ABIReturn), tx_id: str | None = None) → [ABIResult](#algokit_utils.applications.abi.ABIResult)

### algokit_utils.applications.abi.extract_abi_return_from_logs(confirmation: ConfirmationResponse, method: Arc56Method) → [ABIReturn](#algokit_utils.applications.abi.ABIReturn)

Decode ABI return value from a transaction confirmation log.

### algokit_utils.applications.abi.parse_abi_method_result(method: Arc56Method, tx_id: str, txn: ConfirmationResponse) → [ABIResult](#algokit_utils.applications.abi.ABIResult)

Deprecated: use extract_abi_return_from_logs instead.

### algokit_utils.applications.abi.get_arc56_value(abi_return: [ABIReturn](#algokit_utils.applications.abi.ABIReturn), method: algokit_abi.arc56.Method, structs: dict[str, object] | None = None) → Arc56ReturnValueType

Deprecated: use ABIReturn.value instead.

### algokit_utils.applications.abi.get_abi_encoded_value(value: object, abi_type: algokit_abi.ABIType | algokit_abi.arc56.AVMType) → bytes

Encodes a value according to its ABI type.

* **Parameters:**
  * **value** – The value to encode
  * **abi_type** – The ABI or AVM type
* **Returns:**
  The ABI encoded bytes

### algokit_utils.applications.abi.get_abi_decoded_value(value: bytes | int | str, decode_type: algokit_abi.arc56.AVMType | algokit_abi.ABIType | algokit_abi.arc56.ReferenceType) → ABIValue

Decodes a value according to its ABI type.

* **Parameters:**
  * **value** – The value to decode
  * **decode_type** – The ABI type string or type object
* **Returns:**
  The decoded ABI value

### algokit_utils.applications.abi.prepare_value_for_atc(value: Any, abi_type: algokit_abi.ABIType) → Any

Recursively converts any structs present in value to a tuple,
so it can be encoded by algosdk (which does not natively support structs)

TODO: can remove this function once algosdk is removed from transact as algokit_abi supports struct natively

### *class* algokit_utils.applications.abi.BoxABIValue

Represents an ABI value stored in a box.

#### name *: [algokit_utils.models.state.BoxName](../../models/state/index.md#algokit_utils.models.state.BoxName)*

The name of the box

#### value *: ABIValue*

The ABI value stored in the box
