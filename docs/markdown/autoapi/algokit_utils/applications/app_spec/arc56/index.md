# algokit_utils.applications.app_spec.arc56

## Attributes

| [`VoidType`](#algokit_utils.applications.app_spec.arc56.VoidType)         |    |
|---------------------------------------------------------------------------|----|
| [`Void`](#algokit_utils.applications.app_spec.arc56.Void)                 |    |
| [`ENUM_ALIASES`](#algokit_utils.applications.app_spec.arc56.ENUM_ALIASES) |    |

## Classes

| [`AVMType`](#algokit_utils.applications.app_spec.arc56.AVMType)                     | Enum representing native AVM types                                     |
|-------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`CallEnum`](#algokit_utils.applications.app_spec.arc56.CallEnum)                   | Enum representing different call types for application transactions.   |
| [`CreateEnum`](#algokit_utils.applications.app_spec.arc56.CreateEnum)               | Enum representing different create types for application transactions. |
| [`ReferenceType`](#algokit_utils.applications.app_spec.arc56.ReferenceType)         | str(object='') -> str                                                  |
| [`TransactionType`](#algokit_utils.applications.app_spec.arc56.TransactionType)     | str(object='') -> str                                                  |
| [`DefaultValue`](#algokit_utils.applications.app_spec.arc56.DefaultValue)           | Default value information for method arguments.                        |
| [`Argument`](#algokit_utils.applications.app_spec.arc56.Argument)                   | Represents an argument for an ABI method                               |
| [`Returns`](#algokit_utils.applications.app_spec.arc56.Returns)                     | Represents a return type for an ABI method                             |
| [`Actions`](#algokit_utils.applications.app_spec.arc56.Actions)                     | Method actions information.                                            |
| [`EventArg`](#algokit_utils.applications.app_spec.arc56.EventArg)                   | Event argument information.                                            |
| [`Event`](#algokit_utils.applications.app_spec.arc56.Event)                         | Event information.                                                     |
| [`Boxes`](#algokit_utils.applications.app_spec.arc56.Boxes)                         | Box storage requirements.                                              |
| [`Recommendations`](#algokit_utils.applications.app_spec.arc56.Recommendations)     | Method execution recommendations.                                      |
| [`Method`](#algokit_utils.applications.app_spec.arc56.Method)                       | Represents an ABI method description.                                  |
| [`Compiler`](#algokit_utils.applications.app_spec.arc56.Compiler)                   | Enum representing different compiler types.                            |
| [`ByteCode`](#algokit_utils.applications.app_spec.arc56.ByteCode)                   | Represents the approval and clear program bytecode.                    |
| [`CompilerVersion`](#algokit_utils.applications.app_spec.arc56.CompilerVersion)     | Represents compiler version information.                               |
| [`CompilerInfo`](#algokit_utils.applications.app_spec.arc56.CompilerInfo)           | Information about the compiler used.                                   |
| [`Network`](#algokit_utils.applications.app_spec.arc56.Network)                     | Network-specific application information.                              |
| [`ScratchVariables`](#algokit_utils.applications.app_spec.arc56.ScratchVariables)   | Information about scratch space variables.                             |
| [`Source`](#algokit_utils.applications.app_spec.arc56.Source)                       | Source code for approval and clear programs.                           |
| [`Global`](#algokit_utils.applications.app_spec.arc56.Global)                       | Global state schema.                                                   |
| [`Local`](#algokit_utils.applications.app_spec.arc56.Local)                         | Local state schema.                                                    |
| [`Schema`](#algokit_utils.applications.app_spec.arc56.Schema)                       | Application state schema.                                              |
| [`TemplateVariables`](#algokit_utils.applications.app_spec.arc56.TemplateVariables) | Template variable information.                                         |
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

### *class* algokit_utils.applications.app_spec.arc56.AVMType

Bases: `str`, `enum.Enum`

Enum representing native AVM types

#### BYTES *= 'AVMBytes'*

#### STRING *= 'AVMString'*

#### UINT64 *= 'AVMUint64'*

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

### *class* algokit_utils.applications.app_spec.arc56.ReferenceType

Bases: `str`, `enum.Enum`

str(object=’’) -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object._\_str_\_() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to ‘strict’.

#### ASSET *= 'asset'*

#### ACCOUNT *= 'account'*

#### APPLICATION *= 'application'*

### *class* algokit_utils.applications.app_spec.arc56.TransactionType

Bases: `str`, `enum.Enum`

str(object=’’) -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object._\_str_\_() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to ‘strict’.

#### ANY *= 'txn'*

Any transaction

#### PAY *= 'pay'*

Payment transaction

#### KEYREG *= 'keyreg'*

Key registration transaction

#### ACFG *= 'acfg'*

Asset configuration transaction

#### AXFER *= 'axfer'*

Asset transfer transaction

#### AFRZ *= 'afrz'*

Asset freeze transaction

#### APPL *= 'appl'*

App call transaction, allows creating, deleting, and interacting with an application

### algokit_utils.applications.app_spec.arc56.VoidType

### algokit_utils.applications.app_spec.arc56.Void *: VoidType* *= 'void'*

### algokit_utils.applications.app_spec.arc56.ENUM_ALIASES *: collections.abc.Mapping[str, [ReferenceType](#algokit_utils.applications.app_spec.arc56.ReferenceType) | [TransactionType](#algokit_utils.applications.app_spec.arc56.TransactionType) | VoidType | [AVMType](#algokit_utils.applications.app_spec.arc56.AVMType)]*

### *class* algokit_utils.applications.app_spec.arc56.DefaultValue

Default value information for method arguments.

#### data *: str*

The default value data

#### source *: Literal['box', 'global', 'local', 'literal', 'method']*

The source of the default value

#### type *: [AVMType](#algokit_utils.applications.app_spec.arc56.AVMType) | algokit_abi.ABIType | None* *= None*

The optional type of the default value

### *class* algokit_utils.applications.app_spec.arc56.Argument

Represents an argument for an ABI method

Args:
: \_type (ABIType | ReferenceType | TransactionType | str): ABI type, reference type or transaction type
  name (string, optional): name of this argument
  desc (string, optional): description of this argument

#### type *: algokit_abi.ABIType | [ReferenceType](#algokit_utils.applications.app_spec.arc56.ReferenceType) | [TransactionType](#algokit_utils.applications.app_spec.arc56.TransactionType)*

#### default_value *: [DefaultValue](#algokit_utils.applications.app_spec.arc56.DefaultValue) | None* *= None*

#### desc *: str | None* *= None*

#### name *: str | None* *= None*

#### struct *: str | None* *= None*

### *class* algokit_utils.applications.app_spec.arc56.Returns

Represents a return type for an ABI method

Args:
: \_type (ABIType | VoidType | str): ABI type of this return argument
  desc (string, optional): description of this return argument

#### type *: algokit_abi.ABIType | VoidType*

#### desc *: str | None* *= None*

#### struct *: str | None* *= None*

### *class* algokit_utils.applications.app_spec.arc56.Actions

Method actions information.

#### call *: collections.abc.Sequence[[CallEnum](#algokit_utils.applications.app_spec.arc56.CallEnum)]*

The optional list of allowed call actions

#### create *: collections.abc.Sequence[[CreateEnum](#algokit_utils.applications.app_spec.arc56.CreateEnum)]*

The optional list of allowed create actions

### *class* algokit_utils.applications.app_spec.arc56.EventArg

Event argument information.

#### type *: algokit_abi.ABIType*

The type of the event argument

#### name *: str | None* *= None*

The optional name of the argument

#### desc *: str | None* *= None*

The optional description of the argument

#### struct *: str | None* *= None*

The struct name, references a struct defined on the contract

### *class* algokit_utils.applications.app_spec.arc56.Event

Event information.

#### args *: collections.abc.Sequence[[EventArg](#algokit_utils.applications.app_spec.arc56.EventArg)]*

The list of event arguments

#### name *: str*

The name of the event

#### desc *: str | None* *= None*

The optional description of the event

### *class* algokit_utils.applications.app_spec.arc56.Boxes

Box storage requirements.

#### key *: str*

The box key

#### read_bytes *: int*

The number of bytes to read

#### write_bytes *: int*

The number of bytes to write

#### app *: int | None* *= None*

The optional application ID

### *class* algokit_utils.applications.app_spec.arc56.Recommendations

Method execution recommendations.

#### accounts *: list[str]* *= []*

The optional list of accounts

#### apps *: list[int]* *= []*

The optional list of applications

#### assets *: list[int]* *= []*

The optional list of assets

#### boxes *: [Boxes](#algokit_utils.applications.app_spec.arc56.Boxes) | None* *= None*

The optional box storage requirements

#### inner_transaction_count *: int | None* *= None*

The optional inner transaction count

### *class* algokit_utils.applications.app_spec.arc56.Method

Represents an ABI method description.

Args:
: name (string): name of the method
  args (tuple): tuplet of Argument objects with type, name, and optional description
  returns (Returns): a Returns object with a type and optional description
  desc (string, optional): optional description of the method

#### actions *: [Actions](#algokit_utils.applications.app_spec.arc56.Actions)*

The allowed actions

#### args *: collections.abc.Sequence[[Argument](#algokit_utils.applications.app_spec.arc56.Argument)]*

The method arguments

#### name *: str*

The method name

#### returns *: [Returns](#algokit_utils.applications.app_spec.arc56.Returns)*

The return information

#### desc *: str | None* *= None*

The optional description

#### events *: collections.abc.Sequence[[Event](#algokit_utils.applications.app_spec.arc56.Event)]* *= ()*

The events the method can raise

#### readonly *: bool | None* *= None*

The flag indicating if method is readonly, None if unknown

#### recommendations *: [Recommendations](#algokit_utils.applications.app_spec.arc56.Recommendations) | None* *= None*

The execution recommendations

#### get_txn_calls() → int

#### *property* signature *: str*

#### *property* selector *: bytes*

Returns the ABI method signature, which is the first four bytes of the
SHA-512/256 hash of the method signature.

Returns:
: bytes: first four bytes of the method signature hash

#### get_selector() → bytes

Compatibility helper matching algosdk ABI Method API.

#### get_signature() → str

Compatibility helper matching algosdk ABI Method API.

#### *static* from_signature(s: str) → [Method](#algokit_utils.applications.app_spec.arc56.Method)

### *class* algokit_utils.applications.app_spec.arc56.Compiler

Bases: `str`, `enum.Enum`

Enum representing different compiler types.

#### ALGOD *= 'algod'*

#### PUYA *= 'puya'*

### *class* algokit_utils.applications.app_spec.arc56.ByteCode

Represents the approval and clear program bytecode.

#### approval *: bytes*

The approval program bytecode

#### clear *: bytes*

The clear program bytecode

### *class* algokit_utils.applications.app_spec.arc56.CompilerVersion

Represents compiler version information.

#### commit_hash *: str | None* *= None*

The git commit hash of the compiler

#### major *: int | None* *= None*

The major version number

#### minor *: int | None* *= None*

The minor version number

#### patch *: int | None* *= None*

The patch version number

### *class* algokit_utils.applications.app_spec.arc56.CompilerInfo

Information about the compiler used.

#### compiler *: [Compiler](#algokit_utils.applications.app_spec.arc56.Compiler)*

The type of compiler used

#### compiler_version *: [CompilerVersion](#algokit_utils.applications.app_spec.arc56.CompilerVersion)*

Version information for the compiler

### *class* algokit_utils.applications.app_spec.arc56.Network

Network-specific application information.

#### app_id *: int*

The application ID on the network

### *class* algokit_utils.applications.app_spec.arc56.ScratchVariables

Information about scratch space variables.

#### slot *: int*

The scratch slot number

#### type

The type of the scratch variable

### *class* algokit_utils.applications.app_spec.arc56.Source

Source code for approval and clear programs.

#### approval *: str*

The base64 encoded approval program source

#### clear *: str*

The base64 encoded clear program source

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

#### bytes *: int*

The number of byte slices in global state

#### ints *: int*

The number of integers in global state

### *class* algokit_utils.applications.app_spec.arc56.Local

Local state schema.

#### bytes *: int*

The number of byte slices in local state

#### ints *: int*

The number of integers in local state

### *class* algokit_utils.applications.app_spec.arc56.Schema

Application state schema.

#### global_state *: [Global](#algokit_utils.applications.app_spec.arc56.Global)*

The global state schema

#### local_state *: [Local](#algokit_utils.applications.app_spec.arc56.Local)*

The local state schema

### *class* algokit_utils.applications.app_spec.arc56.TemplateVariables

Template variable information.

#### type

The type of the template variable

#### value *: str | None* *= None*

The optional value of the template variable

### *class* algokit_utils.applications.app_spec.arc56.PcOffsetMethod

Bases: `str`, `enum.Enum`

PC offset method types.

#### CBLOCKS *= 'cblocks'*

#### NONE *= 'none'*

### *class* algokit_utils.applications.app_spec.arc56.SourceInfo

Source code location information.

#### pc *: list[int]*

The list of program counter values

#### error_message *: str | None* *= None*

The optional error message

#### source *: str | None* *= None*

The optional source code

#### teal *: int | None* *= None*

The optional TEAL version

### *class* algokit_utils.applications.app_spec.arc56.StorageKey

Storage key information.

#### key *: str*

The storage key

#### desc *: str | None* *= None*

The optional description

#### key_type

#### value_type

### *class* algokit_utils.applications.app_spec.arc56.StorageMap

Storage map information.

#### desc *: str | None* *= None*

The optional description

#### prefix *: str | None* *= None*

The optional key prefix

#### key_type

#### value_type

### *class* algokit_utils.applications.app_spec.arc56.Keys

Storage keys for different storage types.

#### box *: dict[str, [StorageKey](#algokit_utils.applications.app_spec.arc56.StorageKey)]*

The box storage keys

#### global_state *: dict[str, [StorageKey](#algokit_utils.applications.app_spec.arc56.StorageKey)]*

The global state storage keys

#### local_state *: dict[str, [StorageKey](#algokit_utils.applications.app_spec.arc56.StorageKey)]*

The local state storage keys

### *class* algokit_utils.applications.app_spec.arc56.Maps

Storage maps for different storage types.

#### box *: dict[str, [StorageMap](#algokit_utils.applications.app_spec.arc56.StorageMap)]*

The box storage maps

#### global_state *: dict[str, [StorageMap](#algokit_utils.applications.app_spec.arc56.StorageMap)]*

The global state storage maps

#### local_state *: dict[str, [StorageMap](#algokit_utils.applications.app_spec.arc56.StorageMap)]*

The local state storage maps

### *class* algokit_utils.applications.app_spec.arc56.State

Application state information.

#### keys *: [Keys](#algokit_utils.applications.app_spec.arc56.Keys)*

The storage keys

#### maps *: [Maps](#algokit_utils.applications.app_spec.arc56.Maps)*

The storage maps

#### schema *: [Schema](#algokit_utils.applications.app_spec.arc56.Schema)*

The state schema

### *class* algokit_utils.applications.app_spec.arc56.ProgramSourceInfo

Program source information.

#### pc_offset_method *: [PcOffsetMethod](#algokit_utils.applications.app_spec.arc56.PcOffsetMethod)*

The PC offset method

#### source_info *: list[[SourceInfo](#algokit_utils.applications.app_spec.arc56.SourceInfo)]*

The list of source info entries

### *class* algokit_utils.applications.app_spec.arc56.SourceInfoModel

Source information for approval and clear programs.

#### approval *: [ProgramSourceInfo](#algokit_utils.applications.app_spec.arc56.ProgramSourceInfo)*

The approval program source info

#### clear *: [ProgramSourceInfo](#algokit_utils.applications.app_spec.arc56.ProgramSourceInfo)*

The clear program source info

### *class* algokit_utils.applications.app_spec.arc56.Arc56Contract

ARC-0056 application specification.

See [https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0056.md](https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0056.md)

#### arcs *: list[int]*

The list of supported ARC version numbers

#### bare_actions *: [Actions](#algokit_utils.applications.app_spec.arc56.Actions)*

The bare call and create actions

#### methods *: list[[Method](#algokit_utils.applications.app_spec.arc56.Method)]*

The list of contract methods

#### name *: str*

The contract name

#### state *: [State](#algokit_utils.applications.app_spec.arc56.State)*

The contract state information

#### structs *: dict[str, algokit_abi.StructType]*

The contract struct definitions

#### byte_code *: [ByteCode](#algokit_utils.applications.app_spec.arc56.ByteCode) | None* *= None*

The optional bytecode for approval and clear programs

#### compiler_info *: [CompilerInfo](#algokit_utils.applications.app_spec.arc56.CompilerInfo) | None* *= None*

The optional compiler information

#### desc *: str | None* *= None*

The optional contract description

#### events *: list[[Event](#algokit_utils.applications.app_spec.arc56.Event)] | None* *= None*

The optional list of contract events

#### networks *: dict[str, [Network](#algokit_utils.applications.app_spec.arc56.Network)] | None* *= None*

The optional network deployment information

#### scratch_variables *: dict[str, [ScratchVariables](#algokit_utils.applications.app_spec.arc56.ScratchVariables)] | None* *= None*

The optional scratch variable information

#### source *: [Source](#algokit_utils.applications.app_spec.arc56.Source) | None* *= None*

The optional source code

#### source_info *: [SourceInfoModel](#algokit_utils.applications.app_spec.arc56.SourceInfoModel) | None* *= None*

The optional source code information

#### template_variables *: dict[str, [TemplateVariables](#algokit_utils.applications.app_spec.arc56.TemplateVariables)] | None* *= None*

The optional template variable information

#### *classmethod* from_dict(application_spec: dict) → [Arc56Contract](#algokit_utils.applications.app_spec.arc56.Arc56Contract)

Create Arc56Contract from dictionary.

* **Parameters:**
  **application_spec** – Dictionary containing contract specification
* **Returns:**
  Arc56Contract instance

#### *static* from_json(application_spec: str) → [Arc56Contract](#algokit_utils.applications.app_spec.arc56.Arc56Contract)

#### to_json(indent: int | None = None) → str

#### dictify() → dict

#### get_arc56_method(method_name_or_signature: str) → [Method](#algokit_utils.applications.app_spec.arc56.Method)
