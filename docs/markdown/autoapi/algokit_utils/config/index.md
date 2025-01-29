# algokit_utils.config

## Attributes

| [`ALGOKIT_PROJECT_ROOT`](#algokit_utils.config.ALGOKIT_PROJECT_ROOT)       |    |
|----------------------------------------------------------------------------|----|
| [`ALGOKIT_CONFIG_FILENAME`](#algokit_utils.config.ALGOKIT_CONFIG_FILENAME) |    |
| [`config`](#algokit_utils.config.config)                                   |    |

## Classes

| [`AlgoKitLogger`](#algokit_utils.config.AlgoKitLogger)     |                                                                            |
|------------------------------------------------------------|----------------------------------------------------------------------------|
| [`UpdatableConfig`](#algokit_utils.config.UpdatableConfig) | Class to manage and update configuration settings for the AlgoKit project. |

## Module Contents

### algokit_utils.config.ALGOKIT_PROJECT_ROOT

### algokit_utils.config.ALGOKIT_CONFIG_FILENAME *= '.algokit.toml'*

### *class* algokit_utils.config.AlgoKitLogger

#### error(message: str, \*args: Any, suppress_log: bool = False, \*\*kwargs: Any) → None

Log an error message, optionally suppressing output

#### exception(message: str, \*args: Any, suppress_log: bool = False, \*\*kwargs: Any) → None

Log an exception message, optionally suppressing output

#### warning(message: str, \*args: Any, suppress_log: bool = False, \*\*kwargs: Any) → None

Log a warning message, optionally suppressing output

#### info(message: str, \*args: Any, suppress_log: bool = False, \*\*kwargs: Any) → None

Log an info message, optionally suppressing output

#### debug(message: str, \*args: Any, suppress_log: bool = False, \*\*kwargs: Any) → None

Log a debug message, optionally suppressing output

#### verbose(message: str, \*args: Any, suppress_log: bool = False, \*\*kwargs: Any) → None

Log a verbose message (maps to debug), optionally suppressing output

### *class* algokit_utils.config.UpdatableConfig

Class to manage and update configuration settings for the AlgoKit project.

Attributes:
: debug (bool): Indicates whether debug mode is enabled.
  project_root (Path | None): The path to the project root directory.
  trace_all (bool): Indicates whether to trace all operations.
  trace_buffer_size_mb (int): The size of the trace buffer in megabytes.
  max_search_depth (int): The maximum depth to search for a specific file.
  populate_app_call_resources (bool): Indicates whether to populate app call resources.

#### *property* logger *: [AlgoKitLogger](#algokit_utils.config.AlgoKitLogger)*

#### *property* debug *: bool*

Returns the debug status.

#### *property* project_root *: pathlib.Path | None*

Returns the project root path.

#### *property* trace_all *: bool*

Indicates whether to store simulation traces for all operations.

#### *property* trace_buffer_size_mb *: int | float*

Returns the size of the trace buffer in megabytes.

#### *property* populate_app_call_resource *: bool*

#### with_debug(func: collections.abc.Callable[[], str | None]) → None

Executes a function with debug mode temporarily enabled.

#### configure(\*, debug: bool | None = None, project_root: pathlib.Path | None = None, trace_all: bool = False, trace_buffer_size_mb: float = 256, max_search_depth: int = 10, populate_app_call_resources: bool = False) → None

Configures various settings for the application.
Please note, when project_root is not specified, by default config will attempt to find the algokit.toml by
scanning the parent directories according to the max_search_depth parameter.
Alternatively value can also be set via the ALGOKIT_PROJECT_ROOT environment variable.
If you are executing the config from an algokit compliant project, you can simply call
config.configure(debug=True).

* **Parameters:**
  * **debug** – Indicates whether debug mode is enabled.
  * **project_root** – The path to the project root directory. Defaults to None.
  * **trace_all** – Indicates whether to trace all operations. Defaults to False. Which implies that
    only the operations that are failed will be traced by default.
  * **trace_buffer_size_mb** – The size of the trace buffer in megabytes. Defaults to 256
  * **max_search_depth** – The maximum depth to search for a specific file. Defaults to 10
  * **populate_app_call_resources** – Indicates whether to populate app call resources. Defaults to False

### algokit_utils.config.config
