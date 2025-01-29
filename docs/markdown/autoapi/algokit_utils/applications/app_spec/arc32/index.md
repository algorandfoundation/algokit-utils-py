# algokit_utils.applications.app_spec.arc32

## Attributes

| [`AppSpecStateDict`](#algokit_utils.applications.app_spec.arc32.AppSpecStateDict)         | Type defining Application Specification state entries                                                           |
|-------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| [`OnCompleteActionName`](#algokit_utils.applications.app_spec.arc32.OnCompleteActionName) | String literals representing on completion transaction types                                                    |
| [`MethodConfigDict`](#algokit_utils.applications.app_spec.arc32.MethodConfigDict)         | Dictionary of dict[OnCompletionActionName, CallConfig] representing allowed actions for each on completion type |
| [`DefaultArgumentType`](#algokit_utils.applications.app_spec.arc32.DefaultArgumentType)   | Literal values describing the types of default argument sources                                                 |
| [`StateDict`](#algokit_utils.applications.app_spec.arc32.StateDict)                       |                                                                                                                 |

## Classes

| [`CallConfig`](#algokit_utils.applications.app_spec.arc32.CallConfig)                   | Describes the type of calls a method can be used for based on {py:class}\`algosdk.transaction.OnComplete\` type   |
|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| [`StructArgDict`](#algokit_utils.applications.app_spec.arc32.StructArgDict)             | dict() -> new empty dictionary                                                                                    |
| [`DefaultArgumentDict`](#algokit_utils.applications.app_spec.arc32.DefaultArgumentDict) | DefaultArgument is a container for any arguments that may                                                         |
| [`MethodHints`](#algokit_utils.applications.app_spec.arc32.MethodHints)                 | MethodHints provides hints to the caller about how to call the method                                             |
| [`Arc32Contract`](#algokit_utils.applications.app_spec.arc32.Arc32Contract)             | ARC-0032 application specification                                                                                |

## Module Contents

### algokit_utils.applications.app_spec.arc32.AppSpecStateDict *: TypeAlias* *= dict[str, dict[str, dict]]*

Type defining Application Specification state entries

### *class* algokit_utils.applications.app_spec.arc32.CallConfig

Bases: `enum.IntFlag`

Describes the type of calls a method can be used for based on {py:class}\`algosdk.transaction.OnComplete\` type

#### NEVER *= 0*

Never handle the specified on completion type

#### CALL *= 1*

Only handle the specified on completion type for application calls

#### CREATE *= 2*

Only handle the specified on completion type for application create calls

#### ALL *= 3*

Handle the specified on completion type for both create and normal application calls

### *class* algokit_utils.applications.app_spec.arc32.StructArgDict

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

#### name *: str*

#### elements *: list[list[str]]*

### algokit_utils.applications.app_spec.arc32.OnCompleteActionName *: TypeAlias* *= Literal['no_op', 'opt_in', 'close_out', 'clear_state', 'update_application', 'delete_application']*

String literals representing on completion transaction types

### algokit_utils.applications.app_spec.arc32.MethodConfigDict *: TypeAlias* *= dict[OnCompleteActionName, CallConfig]*

Dictionary of dict[OnCompletionActionName, CallConfig] representing allowed actions for each on completion type

### algokit_utils.applications.app_spec.arc32.DefaultArgumentType *: TypeAlias* *= Literal['abi-method', 'local-state', 'global-state', 'constant']*

Literal values describing the types of default argument sources

### *class* algokit_utils.applications.app_spec.arc32.DefaultArgumentDict

Bases: `TypedDict`

DefaultArgument is a container for any arguments that may
be resolved prior to calling some target method

#### source *: DefaultArgumentType*

#### data *: int | str | bytes | algosdk.abi.method.MethodDict*

### algokit_utils.applications.app_spec.arc32.StateDict

### *class* algokit_utils.applications.app_spec.arc32.MethodHints

MethodHints provides hints to the caller about how to call the method

#### read_only *: bool* *= False*

#### structs *: dict[str, [StructArgDict](#algokit_utils.applications.app_spec.arc32.StructArgDict)]*

#### default_arguments *: dict[str, [DefaultArgumentDict](#algokit_utils.applications.app_spec.arc32.DefaultArgumentDict)]*

#### call_config *: MethodConfigDict*

#### empty() → bool

#### dictify() → dict[str, Any]

#### *static* undictify(data: dict[str, Any]) → [MethodHints](#algokit_utils.applications.app_spec.arc32.MethodHints)

### *class* algokit_utils.applications.app_spec.arc32.Arc32Contract

ARC-0032 application specification

See <[https://github.com/algorandfoundation/ARCs/pull/150](https://github.com/algorandfoundation/ARCs/pull/150)>

#### approval_program *: str*

#### clear_program *: str*

#### contract *: algosdk.abi.Contract*

#### hints *: dict[str, [MethodHints](#algokit_utils.applications.app_spec.arc32.MethodHints)]*

#### schema *: StateDict*

#### global_state_schema *: algosdk.transaction.StateSchema*

#### local_state_schema *: algosdk.transaction.StateSchema*

#### bare_call_config *: MethodConfigDict*

#### dictify() → dict

#### to_json(indent: int | None = None) → str

#### *static* from_json(application_spec: str) → [Arc32Contract](#algokit_utils.applications.app_spec.arc32.Arc32Contract)

#### export(directory: pathlib.Path | str | None = None) → None

Write out the artifacts generated by the application to disk.

Writes the approval program, clear program, contract specification and application specification
to files in the specified directory.

* **Parameters:**
  **directory** – Path to the directory where the artifacts should be written. If not specified,
  uses the current working directory
