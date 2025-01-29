# algokit_utils.applications.app_manager

## Attributes

| [`UPDATABLE_TEMPLATE_NAME`](#algokit_utils.applications.app_manager.UPDATABLE_TEMPLATE_NAME)   | The name of the TEAL template variable for deploy-time immutability control.   |
|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`DELETABLE_TEMPLATE_NAME`](#algokit_utils.applications.app_manager.DELETABLE_TEMPLATE_NAME)   | The name of the TEAL template variable for deploy-time permanence control.     |

## Classes

| [`AppManager`](#algokit_utils.applications.app_manager.AppManager)   | A manager class for interacting with Algorand applications.   |
|----------------------------------------------------------------------|---------------------------------------------------------------|

## Module Contents

### algokit_utils.applications.app_manager.UPDATABLE_TEMPLATE_NAME *= 'TMPL_UPDATABLE'*

The name of the TEAL template variable for deploy-time immutability control.

### algokit_utils.applications.app_manager.DELETABLE_TEMPLATE_NAME *= 'TMPL_DELETABLE'*

The name of the TEAL template variable for deploy-time permanence control.

### *class* algokit_utils.applications.app_manager.AppManager(algod_client: algosdk.v2client.algod.AlgodClient)

A manager class for interacting with Algorand applications.

Provides functionality for compiling TEAL code, managing application state,
and interacting with application boxes.

* **Parameters:**
  **algod_client** – The Algorand client instance to use for interacting with the network

#### compile_teal(teal_code: str) → [algokit_utils.models.application.CompiledTeal](../../models/application/index.md#algokit_utils.models.application.CompiledTeal)

Compile TEAL source code.

* **Parameters:**
  **teal_code** – The TEAL source code to compile
* **Returns:**
  The compiled TEAL code and associated metadata

#### compile_teal_template(teal_template_code: str, template_params: algokit_utils.models.state.TealTemplateParams | None = None, deployment_metadata: collections.abc.Mapping[str, bool | None] | None = None) → [algokit_utils.models.application.CompiledTeal](../../models/application/index.md#algokit_utils.models.application.CompiledTeal)

Compile a TEAL template with parameters.

* **Parameters:**
  * **teal_template_code** – The TEAL template code to compile
  * **template_params** – Parameters to substitute in the template
  * **deployment_metadata** – Deployment control parameters
* **Returns:**
  The compiled TEAL code and associated metadata

#### get_compilation_result(teal_code: str) → [algokit_utils.models.application.CompiledTeal](../../models/application/index.md#algokit_utils.models.application.CompiledTeal) | None

Get cached compilation result for TEAL code if available.

* **Parameters:**
  **teal_code** – The TEAL source code
* **Returns:**
  The cached compilation result if available, None otherwise

#### get_by_id(app_id: int) → [algokit_utils.models.application.AppInformation](../../models/application/index.md#algokit_utils.models.application.AppInformation)

Get information about an application by ID.

* **Parameters:**
  **app_id** – The application ID
* **Returns:**
  Information about the application

#### get_global_state(app_id: int) → dict[str, [algokit_utils.models.application.AppState](../../models/application/index.md#algokit_utils.models.application.AppState)]

Get the global state of an application.

* **Parameters:**
  **app_id** – The application ID
* **Returns:**
  The application’s global state

#### get_local_state(app_id: int, address: str) → dict[str, [algokit_utils.models.application.AppState](../../models/application/index.md#algokit_utils.models.application.AppState)]

Get the local state for an account in an application.

* **Parameters:**
  * **app_id** – The application ID
  * **address** – The account address
* **Returns:**
  The account’s local state for the application
* **Raises:**
  **ValueError** – If local state is not found

#### get_box_names(app_id: int) → list[[algokit_utils.models.state.BoxName](../../models/state/index.md#algokit_utils.models.state.BoxName)]

Get names of all boxes for an application.

* **Parameters:**
  **app_id** – The application ID
* **Returns:**
  List of box names

#### get_box_value(app_id: int, box_name: algokit_utils.models.state.BoxIdentifier) → bytes

Get the value stored in a box.

* **Parameters:**
  * **app_id** – The application ID
  * **box_name** – The box identifier
* **Returns:**
  The box value as bytes

#### get_box_values(app_id: int, box_names: list[algokit_utils.models.state.BoxIdentifier]) → list[bytes]

Get values for multiple boxes.

* **Parameters:**
  * **app_id** – The application ID
  * **box_names** – List of box identifiers
* **Returns:**
  List of box values as bytes

#### get_box_value_from_abi_type(app_id: int, box_name: algokit_utils.models.state.BoxIdentifier, abi_type: algokit_utils.applications.abi.ABIType) → algokit_utils.applications.abi.ABIValue

Get and decode a box value using an ABI type.

* **Parameters:**
  * **app_id** – The application ID
  * **box_name** – The box identifier
  * **abi_type** – The ABI type to decode with
* **Returns:**
  The decoded box value
* **Raises:**
  **ValueError** – If decoding fails

#### get_box_values_from_abi_type(app_id: int, box_names: list[algokit_utils.models.state.BoxIdentifier], abi_type: algokit_utils.applications.abi.ABIType) → list[algokit_utils.applications.abi.ABIValue]

Get and decode multiple box values using an ABI type.

* **Parameters:**
  * **app_id** – The application ID
  * **box_names** – List of box identifiers
  * **abi_type** – The ABI type to decode with
* **Returns:**
  List of decoded box values

#### *static* get_box_reference(box_id: algokit_utils.models.state.BoxIdentifier | [algokit_utils.models.state.BoxReference](../../models/state/index.md#algokit_utils.models.state.BoxReference)) → tuple[int, bytes]

Get standardized box reference from various identifier types.

* **Parameters:**
  **box_id** – The box identifier
* **Returns:**
  Tuple of (app_id, box_name_bytes)
* **Raises:**
  **ValueError** – If box identifier type is invalid

#### *static* get_abi_return(confirmation: algosdk.v2client.algod.AlgodResponseType, method: algosdk.abi.Method | None = None) → [algokit_utils.applications.abi.ABIReturn](../abi/index.md#algokit_utils.applications.abi.ABIReturn) | None

Get the ABI return value from a transaction confirmation.

* **Parameters:**
  * **confirmation** – The transaction confirmation
  * **method** – The ABI method
* **Returns:**
  The parsed ABI return value, or None if not available

#### *static* decode_app_state(state: list[dict[str, Any]]) → dict[str, [algokit_utils.models.application.AppState](../../models/application/index.md#algokit_utils.models.application.AppState)]

Decode application state from raw format.

* **Parameters:**
  **state** – The raw application state
* **Returns:**
  Decoded application state
* **Raises:**
  **ValueError** – If unknown state data type is encountered

#### *static* replace_template_variables(program: str, template_values: algokit_utils.models.state.TealTemplateParams) → str

Replace template variables in TEAL code.

* **Parameters:**
  * **program** – The TEAL program code
  * **template_values** – Template variable values to substitute
* **Returns:**
  TEAL code with substituted values
* **Raises:**
  **ValueError** – If template value type is unexpected

#### *static* replace_teal_template_deploy_time_control_params(teal_template_code: str, params: collections.abc.Mapping[str, bool | None]) → str

Replace deploy-time control parameters in TEAL template.

* **Parameters:**
  * **teal_template_code** – The TEAL template code
  * **params** – The deploy-time control parameters
* **Returns:**
  TEAL code with substituted control parameters
* **Raises:**
  **ValueError** – If template variables not found in code

#### *static* strip_teal_comments(teal_code: str) → str
