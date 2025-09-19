# algokit_utils.applications.abi

## Attributes

| [`ABIValue`](#algokit_utils.applications.abi.ABIValue)                         |    |
|--------------------------------------------------------------------------------|----|
| [`ABIStruct`](#algokit_utils.applications.abi.ABIStruct)                       |    |
| [`Arc56ReturnValueType`](#algokit_utils.applications.abi.Arc56ReturnValueType) |    |
| [`ABIType`](#algokit_utils.applications.abi.ABIType)                           |    |
| [`ABIArgumentType`](#algokit_utils.applications.abi.ABIArgumentType)           |    |

## Classes

| [`ABIReturn`](ABIReturn.md#algokit_utils.applications.abi.ABIReturn)       | Represents the return value from an ABI method call.   |
|----------------------------------------------------------------------------|--------------------------------------------------------|
| [`BoxABIValue`](BoxABIValue.md#algokit_utils.applications.abi.BoxABIValue) | Represents an ABI value stored in a box.               |

## Functions

| [`get_arc56_value`](#algokit_utils.applications.abi.get_arc56_value)(→ Arc56ReturnValueType)                                          | Gets the ARC-56 formatted return value from an ABI return.   |
|---------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| [`get_abi_encoded_value`](#algokit_utils.applications.abi.get_abi_encoded_value)(→ bytes)                                             | Encodes a value according to its ABI type.                   |
| [`get_abi_decoded_value`](#algokit_utils.applications.abi.get_abi_decoded_value)(→ ABIValue)                                          | Decodes a value according to its ABI type.                   |
| [`get_abi_tuple_from_abi_struct`](#algokit_utils.applications.abi.get_abi_tuple_from_abi_struct)(→ list[Any])                         | Converts an ABI struct to a tuple representation.            |
| [`get_abi_tuple_type_from_abi_struct_definition`](#algokit_utils.applications.abi.get_abi_tuple_type_from_abi_struct_definition)(...) | Creates a TupleType from a struct definition.                |
| [`get_abi_struct_from_abi_tuple`](#algokit_utils.applications.abi.get_abi_struct_from_abi_tuple)(→ dict[str, Any])                    | Converts a decoded tuple to an ABI struct.                   |

## Module Contents

### *type* algokit_utils.applications.abi.ABIValue *= bool | int | str | bytes | bytearray | list['ABIValue'] | tuple['ABIValue'] | dict[str, 'ABIValue']*

### *type* algokit_utils.applications.abi.ABIStruct *= dict[str, list[dict[str, 'ABIValue']]]*

### *type* algokit_utils.applications.abi.Arc56ReturnValueType *= ABIValue | ABIStruct | None*

### *type* algokit_utils.applications.abi.ABIType *= algosdk.abi.ABIType*

### *type* algokit_utils.applications.abi.ABIArgumentType *= algosdk.abi.ABIType | algosdk.abi.ABITransactionType | algosdk.abi.ABIReferenceType*

### algokit_utils.applications.abi.get_arc56_value(abi_return: [ABIReturn](ABIReturn.md#algokit_utils.applications.abi.ABIReturn), method: [algokit_utils.applications.app_spec.arc56.Method](../app_spec/arc56/Method.md#algokit_utils.applications.app_spec.arc56.Method) | algosdk.abi.method.Method, structs: dict[str, list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)]]) → Arc56ReturnValueType

Gets the ARC-56 formatted return value from an ABI return.

* **Parameters:**
  * **abi_return** – The ABI return value to decode
  * **method** – The ABI method definition
  * **structs** – Dictionary of struct definitions
* **Raises:**
  **ValueError** – If there was an error decoding the return value
* **Returns:**
  The decoded return value in ARC-56 format

### algokit_utils.applications.abi.get_abi_encoded_value(value: Any, type_str: str, structs: dict[str, list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)]]) → bytes

Encodes a value according to its ABI type.

* **Parameters:**
  * **value** – The value to encode
  * **type_str** – The ABI type string
  * **structs** – Dictionary of struct definitions
* **Raises:**
  **ValueError** – If the value cannot be encoded for the given type
* **Returns:**
  The ABI encoded bytes

### algokit_utils.applications.abi.get_abi_decoded_value(value: bytes | int | str, type_str: str | ABIArgumentType, structs: dict[str, list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)]]) → ABIValue

Decodes a value according to its ABI type.

* **Parameters:**
  * **value** – The value to decode
  * **type_str** – The ABI type string or type object
  * **structs** – Dictionary of struct definitions
* **Returns:**
  The decoded ABI value

### algokit_utils.applications.abi.get_abi_tuple_from_abi_struct(struct_value: dict[str, Any], struct_fields: list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)], structs: dict[str, list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)]]) → list[Any]

Converts an ABI struct to a tuple representation.

* **Parameters:**
  * **struct_value** – The struct value as a dictionary
  * **struct_fields** – List of struct field definitions
  * **structs** – Dictionary of struct definitions
* **Raises:**
  **ValueError** – If a required field is missing from the struct
* **Returns:**
  The struct as a tuple

### algokit_utils.applications.abi.get_abi_tuple_type_from_abi_struct_definition(struct_def: list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)], structs: dict[str, list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)]]) → algosdk.abi.TupleType

Creates a TupleType from a struct definition.

* **Parameters:**
  * **struct_def** – The struct field definitions
  * **structs** – Dictionary of struct definitions
* **Raises:**
  **ValueError** – If a field type is invalid
* **Returns:**
  The TupleType representing the struct

### algokit_utils.applications.abi.get_abi_struct_from_abi_tuple(decoded_tuple: Any, struct_fields: list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)], structs: dict[str, list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)]]) → dict[str, Any]

Converts a decoded tuple to an ABI struct.

* **Parameters:**
  * **decoded_tuple** – The tuple to convert
  * **struct_fields** – List of struct field definitions
  * **structs** – Dictionary of struct definitions
* **Returns:**
  The tuple as a struct dictionary
