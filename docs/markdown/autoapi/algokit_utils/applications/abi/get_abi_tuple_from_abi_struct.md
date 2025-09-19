# algokit_utils.applications.abi.get_abi_tuple_from_abi_struct

#### algokit_utils.applications.abi.get_abi_tuple_from_abi_struct(struct_value: dict[str, Any], struct_fields: list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)], structs: dict[str, list[[algokit_utils.applications.app_spec.arc56.StructField](../app_spec/arc56/StructField.md#algokit_utils.applications.app_spec.arc56.StructField)]]) → list[Any]

Converts an ABI struct to a tuple representation.

* **Parameters:**
  * **struct_value** – The struct value as a dictionary
  * **struct_fields** – List of struct field definitions
  * **structs** – Dictionary of struct definitions
* **Raises:**
  **ValueError** – If a required field is missing from the struct
* **Returns:**
  The struct as a tuple
