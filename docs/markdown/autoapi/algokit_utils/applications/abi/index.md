# algokit_utils.applications.abi

## Attributes

| [`ABIValue`](#algokit_utils.applications.abi.ABIValue)                         |    |
|--------------------------------------------------------------------------------|----|
| [`ABIStruct`](#algokit_utils.applications.abi.ABIStruct)                       |    |
| [`Arc56ReturnValueType`](#algokit_utils.applications.abi.Arc56ReturnValueType) |    |
| [`ABIType`](#algokit_utils.applications.abi.ABIType)                           |    |
| [`ABIArgumentType`](#algokit_utils.applications.abi.ABIArgumentType)           |    |

## Classes

| [`ABIResult`](#algokit_utils.applications.abi.ABIResult)     |                                                      |
|--------------------------------------------------------------|------------------------------------------------------|
| [`ABIReturn`](#algokit_utils.applications.abi.ABIReturn)     | Represents the return value from an ABI method call. |
| [`BoxABIValue`](#algokit_utils.applications.abi.BoxABIValue) | Represents an ABI value stored in a box.             |

## Functions

| [`parse_abi_method_result`](#algokit_utils.applications.abi.parse_abi_method_result)(→ ABIResult)   |                                                               |
|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| [`get_arc56_value`](#algokit_utils.applications.abi.get_arc56_value)(→ Arc56ReturnValueType)        | Gets the ARC-56 formatted return value from an ABI return.    |
| [`get_abi_encoded_value`](#algokit_utils.applications.abi.get_abi_encoded_value)(→ bytes)           | Encodes a value according to its ABI type.                    |
| [`get_abi_decoded_value`](#algokit_utils.applications.abi.get_abi_decoded_value)(→ ABIValue)        | Decodes a value according to its ABI type.                    |
| [`prepare_value_for_atc`](#algokit_utils.applications.abi.prepare_value_for_atc)(→ Any)             | Recursively converts any structs present in value to a tuple, |

## Module Contents

### *type* algokit_utils.applications.abi.ABIValue *= bool | int | str | bytes | bytearray | list['ABIValue'] | tuple['ABIValue'] | dict[str, 'ABIValue']*

### *type* algokit_utils.applications.abi.ABIStruct *= dict[str, list[dict[str, 'ABIValue']]]*

### *type* algokit_utils.applications.abi.Arc56ReturnValueType *= ABIValue | ABIStruct | None*

### *type* algokit_utils.applications.abi.ABIType *= algokit_abi.ABIType*

### *type* algokit_utils.applications.abi.ABIArgumentType *= algokit_abi.ABIType | [arc56.TransactionType](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.TransactionType) | [arc56.ReferenceType](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.ReferenceType)*

### *class* algokit_utils.applications.abi.ABIResult

#### tx_id *: str*

#### raw_value *: bytes*

#### return_value *: ABIValue | None*

#### decode_error *: Exception | None*

#### tx_info *: ConfirmationResponse*

#### method *: AlgorandABIMethod*

### algokit_utils.applications.abi.parse_abi_method_result(method: AlgorandABIMethod, tx_id: str, txn: ConfirmationResponse) → [ABIResult](#algokit_utils.applications.abi.ABIResult)

### *class* algokit_utils.applications.abi.ABIReturn(result: [ABIResult](#algokit_utils.applications.abi.ABIResult))

Represents the return value from an ABI method call.

Wraps the raw return value and decoded value along with any decode errors.

#### raw_value *: bytes | None* *= None*

The raw return value from the method call

#### value *: ABIValue | None* *= None*

The decoded return value from the method call

#### method *: AlgorandABIMethod | None* *= None*

The ABI method definition

#### decode_error *: Exception | None* *= None*

The exception that occurred during decoding, if any

#### tx_info *: ConfirmationResponse | None* *= None*

The transaction info for the method call

#### *property* is_success *: bool*

Returns True if the ABI call was successful (no decode error)

* **Returns:**
  True if no decode error occurred, False otherwise

#### get_arc56_value(method: [algokit_utils.applications.app_spec.arc56.Method](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Method)) → Arc56ReturnValueType

Gets the ARC-56 formatted return value.

* **Parameters:**
  **method** – The ABI method definition
* **Returns:**
  The decoded return value in ARC-56 format

### algokit_utils.applications.abi.get_arc56_value(abi_return: [ABIReturn](#algokit_utils.applications.abi.ABIReturn), method: [algokit_utils.applications.app_spec.arc56.Method](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.Method)) → Arc56ReturnValueType

Gets the ARC-56 formatted return value from an ABI return.

* **Parameters:**
  * **abi_return** – The ABI return value to decode
  * **method** – The ABI method definition
* **Raises:**
  **ValueError** – If there was an error decoding the return value
* **Returns:**
  The decoded return value in ARC-56 format

### algokit_utils.applications.abi.get_abi_encoded_value(value: object, abi_type: algokit_abi.ABIType | [algokit_utils.applications.app_spec.arc56.AVMType](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.AVMType)) → bytes

Encodes a value according to its ABI type.

* **Parameters:**
  * **value** – The value to encode
  * **abi_type** – The ABI or AVM type
* **Returns:**
  The ABI encoded bytes

### algokit_utils.applications.abi.get_abi_decoded_value(value: bytes | int | str, decode_type: [algokit_utils.applications.app_spec.arc56.AVMType](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.AVMType) | algokit_abi.ABIType | [algokit_utils.applications.app_spec.arc56.ReferenceType](../app_spec/arc56/index.md#algokit_utils.applications.app_spec.arc56.ReferenceType)) → ABIValue

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
