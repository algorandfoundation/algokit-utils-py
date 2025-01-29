# algokit_utils.applications.app_spec.arc56

## Classes

| [`StructField`](#algokit_utils.applications.app_spec.arc56.StructField)             | Represents a field in a struct type.                                   |
|-------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`CallEnum`](#algokit_utils.applications.app_spec.arc56.CallEnum)                   | Enum representing different call types for application transactions.   |
| [`CreateEnum`](#algokit_utils.applications.app_spec.arc56.CreateEnum)               | Enum representing different create types for application transactions. |
| [`BareActions`](#algokit_utils.applications.app_spec.arc56.BareActions)             | Represents bare call and create actions for an application.            |
| [`ByteCode`](#algokit_utils.applications.app_spec.arc56.ByteCode)                   | Represents the approval and clear program bytecode.                    |
| [`Compiler`](#algokit_utils.applications.app_spec.arc56.Compiler)                   | Enum representing different compiler types.                            |
| [`CompilerVersion`](#algokit_utils.applications.app_spec.arc56.CompilerVersion)     | Represents compiler version information.                               |
| [`CompilerInfo`](#algokit_utils.applications.app_spec.arc56.CompilerInfo)           | Information about the compiler used.                                   |
| [`Network`](#algokit_utils.applications.app_spec.arc56.Network)                     | Network-specific application information.                              |
| [`ScratchVariables`](#algokit_utils.applications.app_spec.arc56.ScratchVariables)   | Information about scratch space variables.                             |
| [`Source`](#algokit_utils.applications.app_spec.arc56.Source)                       | Source code for approval and clear programs.                           |
| [`Global`](#algokit_utils.applications.app_spec.arc56.Global)                       | Global state schema.                                                   |
| [`Local`](#algokit_utils.applications.app_spec.arc56.Local)                         | Local state schema.                                                    |
| [`Schema`](#algokit_utils.applications.app_spec.arc56.Schema)                       | Application state schema.                                              |
| [`TemplateVariables`](#algokit_utils.applications.app_spec.arc56.TemplateVariables) | Template variable information.                                         |
| [`EventArg`](#algokit_utils.applications.app_spec.arc56.EventArg)                   | Event argument information.                                            |
| [`Event`](#algokit_utils.applications.app_spec.arc56.Event)                         | Event information.                                                     |
| [`Actions`](#algokit_utils.applications.app_spec.arc56.Actions)                     | Method actions information.                                            |
| [`DefaultValue`](#algokit_utils.applications.app_spec.arc56.DefaultValue)           | Default value information for method arguments.                        |
| [`MethodArg`](#algokit_utils.applications.app_spec.arc56.MethodArg)                 | Method argument information.                                           |
| [`Boxes`](#algokit_utils.applications.app_spec.arc56.Boxes)                         | Box storage requirements.                                              |
| [`Recommendations`](#algokit_utils.applications.app_spec.arc56.Recommendations)     | Method execution recommendations.                                      |
| [`Returns`](#algokit_utils.applications.app_spec.arc56.Returns)                     | Method return information.                                             |
| [`Method`](#algokit_utils.applications.app_spec.arc56.Method)                       | Method information.                                                    |
| [`PcOffsetMethod`](#algokit_utils.applications.app_spec.arc56.PcOffsetMethod)       | PC offset method types.                                                |
| [`SourceInfo`](#algokit_utils.applications.app_spec.arc56.SourceInfo)               | Source code location information.                                      |
| [`StorageKey`](#algokit_utils.applications.app_spec.arc56.StorageKey)               | Storage key information.                                               |
| [`StorageMap`](#algokit_utils.applications.app_spec.arc56.StorageMap)               | Storage map information.                                               |
| [`Keys`](#algokit_utils.applications.app_spec.arc56.Keys)                           | Storage keys for different storage types.                              |
| [`Maps`](#algokit_utils.applications.app_spec.arc56.Maps)                           | Storage maps for different storage types.                              |
| [`State`](#algokit_utils.applications.app_spec.arc56.State)                         | Application state information.                                         |
| [`ProgramSourceInfo`](#algokit_utils.applications.app_spec.arc56.ProgramSourceInfo) | Program source information.                                            |
| [`SourceInfoModel`](#algokit_utils.applications.app_spec.arc56.SourceInfoModel)     | Source information for approval and clear programs.                    |
| [`Arc56Contract`](#algokit_utils.applications.app_spec.arc56.Arc56Contract)         | ARC-0056 application specification.                                    |

## Module Contents

### *class* algokit_utils.applications.app_spec.arc56.StructField

Represents a field in a struct type.

* **Variables:**
  * **name** – Name of the struct field
  * **type** – Type of the struct field, either a string or list of StructFields

#### name *: str*

#### type *: list[[StructField](#algokit_utils.applications.app_spec.arc56.StructField)] | str*

#### *static* from_dict(data: dict[str, Any]) → [StructField](#algokit_utils.applications.app_spec.arc56.StructField)

### *class* algokit_utils.applications.app_spec.arc56.CallEnum

Bases: `str`, `enum.Enum`

Enum representing different call types for application transactions.

#### CLEAR_STATE *= 'ClearState'*

#### CLOSE_OUT *= 'CloseOut'*

#### DELETE_APPLICATION *= 'DeleteApplication'*

#### NO_OP *= 'NoOp'*

#### OPT_IN *= 'OptIn'*

#### UPDATE_APPLICATION *= 'UpdateApplication'*

### *class* algokit_utils.applications.app_spec.arc56.CreateEnum

Bases: `str`, `enum.Enum`

Enum representing different create types for application transactions.

#### DELETE_APPLICATION *= 'DeleteApplication'*

#### NO_OP *= 'NoOp'*

#### OPT_IN *= 'OptIn'*

### *class* algokit_utils.applications.app_spec.arc56.BareActions

Represents bare call and create actions for an application.

* **Variables:**
  * **call** – List of allowed call actions
  * **create** – List of allowed create actions

#### call *: list[[CallEnum](#algokit_utils.applications.app_spec.arc56.CallEnum)]*

#### create *: list[[CreateEnum](#algokit_utils.applications.app_spec.arc56.CreateEnum)]*

#### *static* from_dict(data: dict[str, Any]) → [BareActions](#algokit_utils.applications.app_spec.arc56.BareActions)

### *class* algokit_utils.applications.app_spec.arc56.ByteCode

Represents the approval and clear program bytecode.

* **Variables:**
  * **approval** – Base64 encoded approval program bytecode
  * **clear** – Base64 encoded clear program bytecode

#### approval *: str*

#### clear *: str*

#### *static* from_dict(data: dict[str, Any]) → [ByteCode](#algokit_utils.applications.app_spec.arc56.ByteCode)

### *class* algokit_utils.applications.app_spec.arc56.Compiler

Bases: `str`, `enum.Enum`

Enum representing different compiler types.

#### ALGOD *= 'algod'*

#### PUYA *= 'puya'*

### *class* algokit_utils.applications.app_spec.arc56.CompilerVersion

Represents compiler version information.

* **Variables:**
  * **commit_hash** – Git commit hash of the compiler
  * **major** – Major version number
  * **minor** – Minor version number
  * **patch** – Patch version number

#### commit_hash *: str | None* *= None*

#### major *: int | None* *= None*

#### minor *: int | None* *= None*

#### patch *: int | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [CompilerVersion](#algokit_utils.applications.app_spec.arc56.CompilerVersion)

### *class* algokit_utils.applications.app_spec.arc56.CompilerInfo

Information about the compiler used.

* **Variables:**
  * **compiler** – Type of compiler used
  * **compiler_version** – Version information for the compiler

#### compiler *: [Compiler](#algokit_utils.applications.app_spec.arc56.Compiler)*

#### compiler_version *: [CompilerVersion](#algokit_utils.applications.app_spec.arc56.CompilerVersion)*

#### *static* from_dict(data: dict[str, Any]) → [CompilerInfo](#algokit_utils.applications.app_spec.arc56.CompilerInfo)

### *class* algokit_utils.applications.app_spec.arc56.Network

Network-specific application information.

* **Variables:**
  **app_id** – Application ID on the network

#### app_id *: int*

#### *static* from_dict(data: dict[str, Any]) → [Network](#algokit_utils.applications.app_spec.arc56.Network)

### *class* algokit_utils.applications.app_spec.arc56.ScratchVariables

Information about scratch space variables.

* **Variables:**
  * **slot** – Scratch slot number
  * **type** – Type of the scratch variable

#### slot *: int*

#### type *: str*

#### *static* from_dict(data: dict[str, Any]) → [ScratchVariables](#algokit_utils.applications.app_spec.arc56.ScratchVariables)

### *class* algokit_utils.applications.app_spec.arc56.Source

Source code for approval and clear programs.

* **Variables:**
  * **approval** – Base64 encoded approval program source
  * **clear** – Base64 encoded clear program source

#### approval *: str*

#### clear *: str*

#### *static* from_dict(data: dict[str, Any]) → [Source](#algokit_utils.applications.app_spec.arc56.Source)

#### get_decoded_approval() → str

Get decoded approval program source.

* **Returns:**
  Decoded approval program source code

#### get_decoded_clear() → str

Get decoded clear program source.

* **Returns:**
  Decoded clear program source code

### *class* algokit_utils.applications.app_spec.arc56.Global

Global state schema.

* **Variables:**
  * **bytes** – Number of byte slices in global state
  * **ints** – Number of integers in global state

#### bytes *: int*

#### ints *: int*

#### *static* from_dict(data: dict[str, Any]) → [Global](#algokit_utils.applications.app_spec.arc56.Global)

### *class* algokit_utils.applications.app_spec.arc56.Local

Local state schema.

* **Variables:**
  * **bytes** – Number of byte slices in local state
  * **ints** – Number of integers in local state

#### bytes *: int*

#### ints *: int*

#### *static* from_dict(data: dict[str, Any]) → [Local](#algokit_utils.applications.app_spec.arc56.Local)

### *class* algokit_utils.applications.app_spec.arc56.Schema

Application state schema.

* **Variables:**
  * **global_state** – Global state schema
  * **local_state** – Local state schema

#### global_state *: [Global](#algokit_utils.applications.app_spec.arc56.Global)*

#### local_state *: [Local](#algokit_utils.applications.app_spec.arc56.Local)*

#### *static* from_dict(data: dict[str, Any]) → [Schema](#algokit_utils.applications.app_spec.arc56.Schema)

### *class* algokit_utils.applications.app_spec.arc56.TemplateVariables

Template variable information.

* **Variables:**
  * **type** – Type of the template variable
  * **value** – Optional value of the template variable

#### type *: str*

#### value *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [TemplateVariables](#algokit_utils.applications.app_spec.arc56.TemplateVariables)

### *class* algokit_utils.applications.app_spec.arc56.EventArg

Event argument information.

* **Variables:**
  * **type** – Type of the event argument
  * **desc** – Optional description of the argument
  * **name** – Optional name of the argument
  * **struct** – Optional struct type name

#### type *: str*

#### desc *: str | None* *= None*

#### name *: str | None* *= None*

#### struct *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [EventArg](#algokit_utils.applications.app_spec.arc56.EventArg)

### *class* algokit_utils.applications.app_spec.arc56.Event

Event information.

* **Variables:**
  * **args** – List of event arguments
  * **name** – Name of the event
  * **desc** – Optional description of the event

#### args *: list[[EventArg](#algokit_utils.applications.app_spec.arc56.EventArg)]*

#### name *: str*

#### desc *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [Event](#algokit_utils.applications.app_spec.arc56.Event)

### *class* algokit_utils.applications.app_spec.arc56.Actions

Method actions information.

* **Variables:**
  * **call** – Optional list of allowed call actions
  * **create** – Optional list of allowed create actions

#### call *: list[[CallEnum](#algokit_utils.applications.app_spec.arc56.CallEnum)] | None* *= None*

#### create *: list[[CreateEnum](#algokit_utils.applications.app_spec.arc56.CreateEnum)] | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [Actions](#algokit_utils.applications.app_spec.arc56.Actions)

### *class* algokit_utils.applications.app_spec.arc56.DefaultValue

Default value information for method arguments.

* **Variables:**
  * **data** – Default value data
  * **source** – Source of the default value
  * **type** – Optional type of the default value

#### data *: str*

#### source *: Literal['box', 'global', 'local', 'literal', 'method']*

#### type *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [DefaultValue](#algokit_utils.applications.app_spec.arc56.DefaultValue)

### *class* algokit_utils.applications.app_spec.arc56.MethodArg

Method argument information.

* **Variables:**
  * **type** – Type of the argument
  * **default_value** – Optional default value
  * **desc** – Optional description
  * **name** – Optional name
  * **struct** – Optional struct type name

#### type *: str*

#### default_value *: [DefaultValue](#algokit_utils.applications.app_spec.arc56.DefaultValue) | None* *= None*

#### desc *: str | None* *= None*

#### name *: str | None* *= None*

#### struct *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [MethodArg](#algokit_utils.applications.app_spec.arc56.MethodArg)

### *class* algokit_utils.applications.app_spec.arc56.Boxes

Box storage requirements.

* **Variables:**
  * **key** – Box key
  * **read_bytes** – Number of bytes to read
  * **write_bytes** – Number of bytes to write
  * **app** – Optional application ID

#### key *: str*

#### read_bytes *: int*

#### write_bytes *: int*

#### app *: int | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [Boxes](#algokit_utils.applications.app_spec.arc56.Boxes)

### *class* algokit_utils.applications.app_spec.arc56.Recommendations

Method execution recommendations.

* **Variables:**
  * **accounts** – Optional list of accounts
  * **apps** – Optional list of applications
  * **assets** – Optional list of assets
  * **boxes** – Optional box storage requirements
  * **inner_transaction_count** – Optional inner transaction count

#### accounts *: list[str] | None* *= None*

#### apps *: list[int] | None* *= None*

#### assets *: list[int] | None* *= None*

#### boxes *: [Boxes](#algokit_utils.applications.app_spec.arc56.Boxes) | None* *= None*

#### inner_transaction_count *: int | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [Recommendations](#algokit_utils.applications.app_spec.arc56.Recommendations)

### *class* algokit_utils.applications.app_spec.arc56.Returns

Method return information.

* **Variables:**
  * **type** – Return type
  * **desc** – Optional description
  * **struct** – Optional struct type name

#### type *: str*

#### desc *: str | None* *= None*

#### struct *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [Returns](#algokit_utils.applications.app_spec.arc56.Returns)

### *class* algokit_utils.applications.app_spec.arc56.Method

Method information.

* **Variables:**
  * **actions** – Allowed actions
  * **args** – Method arguments
  * **name** – Method name
  * **returns** – Return information
  * **desc** – Optional description
  * **events** – Optional list of events
  * **readonly** – Optional readonly flag
  * **recommendations** – Optional execution recommendations

#### actions *: [Actions](#algokit_utils.applications.app_spec.arc56.Actions)*

#### args *: list[[MethodArg](#algokit_utils.applications.app_spec.arc56.MethodArg)]*

#### name *: str*

#### returns *: [Returns](#algokit_utils.applications.app_spec.arc56.Returns)*

#### desc *: str | None* *= None*

#### events *: list[[Event](#algokit_utils.applications.app_spec.arc56.Event)] | None* *= None*

#### readonly *: bool | None* *= None*

#### recommendations *: [Recommendations](#algokit_utils.applications.app_spec.arc56.Recommendations) | None* *= None*

#### to_abi_method() → algosdk.abi.Method

Convert to ABI method.

* **Raises:**
  **ValueError** – If underlying ABI method is not initialized
* **Returns:**
  ABI method

#### *static* from_dict(data: dict[str, Any]) → [Method](#algokit_utils.applications.app_spec.arc56.Method)

### *class* algokit_utils.applications.app_spec.arc56.PcOffsetMethod

Bases: `str`, `enum.Enum`

PC offset method types.

#### CBLOCKS *= 'cblocks'*

#### NONE *= 'none'*

### *class* algokit_utils.applications.app_spec.arc56.SourceInfo

Source code location information.

* **Variables:**
  * **pc** – List of program counter values
  * **error_message** – Optional error message
  * **source** – Optional source code
  * **teal** – Optional TEAL version

#### pc *: list[int]*

#### error_message *: str | None* *= None*

#### source *: str | None* *= None*

#### teal *: int | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [SourceInfo](#algokit_utils.applications.app_spec.arc56.SourceInfo)

### *class* algokit_utils.applications.app_spec.arc56.StorageKey

Storage key information.

* **Variables:**
  * **key** – Storage key
  * **key_type** – Type of the key
  * **value_type** – Type of the value
  * **desc** – Optional description

#### key *: str*

#### key_type *: str*

#### value_type *: str*

#### desc *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [StorageKey](#algokit_utils.applications.app_spec.arc56.StorageKey)

### *class* algokit_utils.applications.app_spec.arc56.StorageMap

Storage map information.

* **Variables:**
  * **key_type** – Type of map keys
  * **value_type** – Type of map values
  * **desc** – Optional description
  * **prefix** – Optional key prefix

#### key_type *: str*

#### value_type *: str*

#### desc *: str | None* *= None*

#### prefix *: str | None* *= None*

#### *static* from_dict(data: dict[str, Any]) → [StorageMap](#algokit_utils.applications.app_spec.arc56.StorageMap)

### *class* algokit_utils.applications.app_spec.arc56.Keys

Storage keys for different storage types.

* **Variables:**
  * **box** – Box storage keys
  * **global_state** – Global state storage keys
  * **local_state** – Local state storage keys

#### box *: dict[str, [StorageKey](#algokit_utils.applications.app_spec.arc56.StorageKey)]*

#### global_state *: dict[str, [StorageKey](#algokit_utils.applications.app_spec.arc56.StorageKey)]*

#### local_state *: dict[str, [StorageKey](#algokit_utils.applications.app_spec.arc56.StorageKey)]*

#### *static* from_dict(data: dict[str, Any]) → [Keys](#algokit_utils.applications.app_spec.arc56.Keys)

### *class* algokit_utils.applications.app_spec.arc56.Maps

Storage maps for different storage types.

* **Variables:**
  * **box** – Box storage maps
  * **global_state** – Global state storage maps
  * **local_state** – Local state storage maps

#### box *: dict[str, [StorageMap](#algokit_utils.applications.app_spec.arc56.StorageMap)]*

#### global_state *: dict[str, [StorageMap](#algokit_utils.applications.app_spec.arc56.StorageMap)]*

#### local_state *: dict[str, [StorageMap](#algokit_utils.applications.app_spec.arc56.StorageMap)]*

#### *static* from_dict(data: dict[str, Any]) → [Maps](#algokit_utils.applications.app_spec.arc56.Maps)

### *class* algokit_utils.applications.app_spec.arc56.State

Application state information.

* **Variables:**
  * **keys** – Storage keys
  * **maps** – Storage maps
  * **schema** – State schema

#### keys *: [Keys](#algokit_utils.applications.app_spec.arc56.Keys)*

#### maps *: [Maps](#algokit_utils.applications.app_spec.arc56.Maps)*

#### schema *: [Schema](#algokit_utils.applications.app_spec.arc56.Schema)*

#### *static* from_dict(data: dict[str, Any]) → [State](#algokit_utils.applications.app_spec.arc56.State)

### *class* algokit_utils.applications.app_spec.arc56.ProgramSourceInfo

Program source information.

* **Variables:**
  * **pc_offset_method** – PC offset method
  * **source_info** – List of source info entries

#### pc_offset_method *: [PcOffsetMethod](#algokit_utils.applications.app_spec.arc56.PcOffsetMethod)*

#### source_info *: list[[SourceInfo](#algokit_utils.applications.app_spec.arc56.SourceInfo)]*

#### *static* from_dict(data: dict[str, Any]) → [ProgramSourceInfo](#algokit_utils.applications.app_spec.arc56.ProgramSourceInfo)

### *class* algokit_utils.applications.app_spec.arc56.SourceInfoModel

Source information for approval and clear programs.

* **Variables:**
  * **approval** – Approval program source info
  * **clear** – Clear program source info

#### approval *: [ProgramSourceInfo](#algokit_utils.applications.app_spec.arc56.ProgramSourceInfo)*

#### clear *: [ProgramSourceInfo](#algokit_utils.applications.app_spec.arc56.ProgramSourceInfo)*

#### *static* from_dict(data: dict[str, Any]) → [SourceInfoModel](#algokit_utils.applications.app_spec.arc56.SourceInfoModel)

### *class* algokit_utils.applications.app_spec.arc56.Arc56Contract

ARC-0056 application specification.

See [https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0056.md](https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0056.md)

* **Variables:**
  * **arcs** – List of supported ARC version numbers
  * **bare_actions** – Bare call and create actions
  * **methods** – List of contract methods
  * **name** – Contract name
  * **state** – Contract state information
  * **structs** – Contract struct definitions
  * **byte_code** – Optional bytecode for approval and clear programs
  * **compiler_info** – Optional compiler information
  * **desc** – Optional contract description
  * **events** – Optional list of contract events
  * **networks** – Optional network deployment information
  * **scratch_variables** – Optional scratch variable information
  * **source** – Optional source code
  * **source_info** – Optional source code information
  * **template_variables** – Optional template variable information

#### arcs *: list[int]*

#### bare_actions *: [BareActions](#algokit_utils.applications.app_spec.arc56.BareActions)*

#### methods *: list[[Method](#algokit_utils.applications.app_spec.arc56.Method)]*

#### name *: str*

#### state *: [State](#algokit_utils.applications.app_spec.arc56.State)*

#### structs *: dict[str, list[[StructField](#algokit_utils.applications.app_spec.arc56.StructField)]]*

#### byte_code *: [ByteCode](#algokit_utils.applications.app_spec.arc56.ByteCode) | None* *= None*

#### compiler_info *: [CompilerInfo](#algokit_utils.applications.app_spec.arc56.CompilerInfo) | None* *= None*

#### desc *: str | None* *= None*

#### events *: list[[Event](#algokit_utils.applications.app_spec.arc56.Event)] | None* *= None*

#### networks *: dict[str, [Network](#algokit_utils.applications.app_spec.arc56.Network)] | None* *= None*

#### scratch_variables *: dict[str, [ScratchVariables](#algokit_utils.applications.app_spec.arc56.ScratchVariables)] | None* *= None*

#### source *: [Source](#algokit_utils.applications.app_spec.arc56.Source) | None* *= None*

#### source_info *: [SourceInfoModel](#algokit_utils.applications.app_spec.arc56.SourceInfoModel) | None* *= None*

#### template_variables *: dict[str, [TemplateVariables](#algokit_utils.applications.app_spec.arc56.TemplateVariables)] | None* *= None*

#### *static* from_dict(application_spec: dict) → [Arc56Contract](#algokit_utils.applications.app_spec.arc56.Arc56Contract)

Create Arc56Contract from dictionary.

* **Parameters:**
  **application_spec** – Dictionary containing contract specification
* **Returns:**
  Arc56Contract instance

#### *static* from_json(application_spec: str) → [Arc56Contract](#algokit_utils.applications.app_spec.arc56.Arc56Contract)

#### *static* from_arc32(arc32_application_spec: str | [algokit_utils.applications.app_spec.arc32.Arc32Contract](../arc32/index.md#algokit_utils.applications.app_spec.arc32.Arc32Contract)) → [Arc56Contract](#algokit_utils.applications.app_spec.arc56.Arc56Contract)

#### *static* get_abi_struct_from_abi_tuple(decoded_tuple: Any, struct_fields: list[[StructField](#algokit_utils.applications.app_spec.arc56.StructField)], structs: dict[str, list[[StructField](#algokit_utils.applications.app_spec.arc56.StructField)]]) → dict[str, Any]

#### to_json(indent: int | None = None) → str

#### dictify() → dict

#### get_arc56_method(method_name_or_signature: str) → [Method](#algokit_utils.applications.app_spec.arc56.Method)
