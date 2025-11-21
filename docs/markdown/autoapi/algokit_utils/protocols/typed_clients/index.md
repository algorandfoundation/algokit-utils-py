# algokit_utils.protocols.typed_clients

## Classes

| [`TypedAppClientProtocol`](#algokit_utils.protocols.typed_clients.TypedAppClientProtocol)   | Base class for protocol classes.   |
|---------------------------------------------------------------------------------------------|------------------------------------|
| [`TypedAppFactoryProtocol`](#algokit_utils.protocols.typed_clients.TypedAppFactoryProtocol) | Base class for protocol classes.   |

## Module Contents

### *class* algokit_utils.protocols.typed_clients.TypedAppClientProtocol(\*, app_id: int, app_name: str | None = None, default_sender: str | None = None, default_signer: [algokit_utils.protocols.signer.TransactionSigner](../signer/index.md#algokit_utils.protocols.signer.TransactionSigner) | None = None, algorand: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient), approval_source_map: algokit_algosdk.source_map.SourceMap | None = None, clear_source_map: algokit_algosdk.source_map.SourceMap | None = None)

Bases: `Protocol`

Base class for protocol classes.

Protocol classes are defined as:

```default
class Proto(Protocol):
    def meth(self) -> int:
        ...
```

Such classes are primarily used with static type checkers that recognize
structural subtyping (static duck-typing), for example:

```default
class C:
    def meth(self) -> int:
        return 0

def func(x: Proto) -> int:
    return x.meth()

func(C())  # Passes static type check
```

See PEP 544 for details. Protocol classes decorated with
@typing.runtime_checkable act as simple-minded runtime protocols that check
only the presence of given attributes, ignoring their type signatures.
Protocol classes can be generic, they are defined as:

```default
class GenProto(Protocol[T]):
    def meth(self) -> T:
        ...
```

#### *classmethod* from_creator_and_name(\*, creator_address: str, app_name: str, default_sender: str | None = None, default_signer: [algokit_utils.protocols.signer.TransactionSigner](../signer/index.md#algokit_utils.protocols.signer.TransactionSigner) | None = None, ignore_cache: bool | None = None, app_lookup_cache: [ApplicationLookup](../../applications/app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None, algorand: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient)) → typing_extensions.Self

#### *classmethod* from_network(\*, app_name: str | None = None, default_sender: str | None = None, default_signer: [algokit_utils.protocols.signer.TransactionSigner](../signer/index.md#algokit_utils.protocols.signer.TransactionSigner) | None = None, approval_source_map: algokit_algosdk.source_map.SourceMap | None = None, clear_source_map: algokit_algosdk.source_map.SourceMap | None = None, algorand: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient)) → typing_extensions.Self

### *class* algokit_utils.protocols.typed_clients.TypedAppFactoryProtocol(algorand: [algokit_utils.algorand.AlgorandClient](../../algorand/index.md#algokit_utils.algorand.AlgorandClient), \*\*kwargs: Any)

Bases: `Protocol`, `Generic`[`CreateParamsT`, `UpdateParamsT`, `DeleteParamsT`]

Base class for protocol classes.

Protocol classes are defined as:

```default
class Proto(Protocol):
    def meth(self) -> int:
        ...
```

Such classes are primarily used with static type checkers that recognize
structural subtyping (static duck-typing), for example:

```default
class C:
    def meth(self) -> int:
        return 0

def func(x: Proto) -> int:
    return x.meth()

func(C())  # Passes static type check
```

See PEP 544 for details. Protocol classes decorated with
@typing.runtime_checkable act as simple-minded runtime protocols that check
only the presence of given attributes, ignoring their type signatures.
Protocol classes can be generic, they are defined as:

```default
class GenProto(Protocol[T]):
    def meth(self) -> T:
        ...
```

#### deploy(\*, on_update: [OnUpdate](../../applications/enums/index.md#algokit_utils.applications.enums.OnUpdate) | None = None, on_schema_break: [OnSchemaBreak](../../applications/enums/index.md#algokit_utils.applications.enums.OnSchemaBreak) | None = None, create_params: CreateParamsT | None = None, update_params: UpdateParamsT | None = None, delete_params: DeleteParamsT | None = None, existing_deployments: [ApplicationLookup](../../applications/app_deployer/index.md#algokit_utils.applications.app_deployer.ApplicationLookup) | None = None, ignore_cache: bool = False, app_name: str | None = None, send_params: [SendParams](../../models/transaction/index.md#algokit_utils.models.transaction.SendParams) | None = None, compilation_params: [AppClientCompilationParams](../../applications/app_client/index.md#algokit_utils.applications.app_client.AppClientCompilationParams) | None = None) → tuple[[TypedAppClientProtocol](#algokit_utils.protocols.typed_clients.TypedAppClientProtocol), [algokit_utils.applications.app_factory.AppFactoryDeployResult](../../applications/app_factory/index.md#algokit_utils.applications.app_factory.AppFactoryDeployResult)]
