# algokit_utils.models.application

## Classes

| [`AppState`](#algokit_utils.models.application.AppState)                         |    |
|----------------------------------------------------------------------------------|----|
| [`AppInformation`](#algokit_utils.models.application.AppInformation)             |    |
| [`CompiledTeal`](#algokit_utils.models.application.CompiledTeal)                 |    |
| [`AppCompilationResult`](#algokit_utils.models.application.AppCompilationResult) |    |
| [`AppSourceMaps`](#algokit_utils.models.application.AppSourceMaps)               |    |

## Module Contents

### *class* algokit_utils.models.application.AppState

#### key_raw *: bytes*

#### key_base64 *: str*

#### value_raw *: bytes | None*

#### value_base64 *: str | None*

#### value *: str | int*

### *class* algokit_utils.models.application.AppInformation

#### app_id *: int*

#### app_address *: str*

#### approval_program *: bytes*

#### clear_state_program *: bytes*

#### creator *: str*

#### global_state *: dict[str, [AppState](#algokit_utils.models.application.AppState)]*

#### local_ints *: int*

#### local_byte_slices *: int*

#### global_ints *: int*

#### global_byte_slices *: int*

#### extra_program_pages *: int | None*

### *class* algokit_utils.models.application.CompiledTeal

#### teal *: str*

#### compiled *: str*

#### compiled_hash *: str*

#### compiled_base64_to_bytes *: bytes*

#### source_map *: algosdk.source_map.SourceMap | None*

### *class* algokit_utils.models.application.AppCompilationResult

#### compiled_approval *: [CompiledTeal](#algokit_utils.models.application.CompiledTeal)*

#### compiled_clear *: [CompiledTeal](#algokit_utils.models.application.CompiledTeal)*

### *class* algokit_utils.models.application.AppSourceMaps

#### approval_source_map *: algosdk.source_map.SourceMap | None* *= None*

#### clear_source_map *: algosdk.source_map.SourceMap | None* *= None*
