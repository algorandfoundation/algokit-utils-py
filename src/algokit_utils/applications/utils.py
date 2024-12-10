import base64
from typing import Any, Literal, TypeVar

from algosdk.abi import Method as AlgorandABIMethod
from algosdk.abi import TupleType
from algosdk.atomic_transaction_composer import ABIResult

from algokit_utils._legacy_v2.application_specification import (
    ApplicationSpecification,
    AppSpecStateDict,
    DefaultArgumentDict,
    MethodConfigDict,
    MethodHints,
)
from algokit_utils.models.abi import ABIStruct, ABIType, ABIValue
from algokit_utils.models.application import (
    ABIArgumentType,
    ABITypeAlias,
    Arc56Contract,
    Arc56ContractState,
    Arc56Method,
    CallConfig,
    DefaultValue,
    Method,
    MethodActions,
    MethodArg,
    MethodReturns,
    OnCompleteAction,
    StorageKey,
    StructField,
    StructName,
)

T = TypeVar("T", bound=ABIValue | bytes | ABIStruct | None)


def get_arc56_method(method_name_or_signature: str, app_spec: Arc56Contract) -> Arc56Method:
    if "(" not in method_name_or_signature:
        # Filter by method name
        methods = [m for m in app_spec.methods if m.name == method_name_or_signature]
        if not methods:
            raise ValueError(f"Unable to find method {method_name_or_signature} in {app_spec.name} app.")
        if len(methods) > 1:
            signatures = [AlgorandABIMethod.undictify(m.__dict__).get_signature() for m in app_spec.methods]
            raise ValueError(
                f"Received a call to method {method_name_or_signature} in contract {app_spec.name}, "
                f"but this resolved to multiple methods; please pass in an ABI signature instead: "
                f"{', '.join(signatures)}"
            )
        method = methods[0]
    else:
        # Find by signature
        method = None
        for m in app_spec.methods:
            abi_method = AlgorandABIMethod.undictify(m.to_dict())
            if abi_method.get_signature() == method_name_or_signature:
                method = m
                break

    if method is None:
        raise ValueError(f"Unable to find method {method_name_or_signature} in {app_spec.name} app.")

    return Arc56Method(method)


def get_arc56_return_value(
    return_value: ABIResult | None,
    method: Method | AlgorandABIMethod,
    structs: dict[str, list[StructField]],
) -> ABIValue | ABIStruct | None:
    """Checks for decode errors on the return value and maps it to the specified type.

    Args:
        return_value: The smart contract response
        method: The method that was called
        structs: The struct fields from the app spec

    Returns:
        The smart contract response with an updated return value

    Raises:
        ValueError: If there is a decode error
    """

    # Get method returns info
    if isinstance(method, AlgorandABIMethod):
        type_str = method.returns.type
        struct = None  # AlgorandABIMethod doesn't have struct info
    else:
        type_str = method.returns.type
        struct = method.returns.struct

    # Handle void/undefined returns
    if type_str == "void" or return_value is None:
        return None

    # Handle decode errors
    if return_value.decode_error:
        raise ValueError(return_value.decode_error)

    # Get raw return value
    raw_value = return_value.raw_value

    # Handle AVM types
    if type_str == "AVMBytes":
        return raw_value
    if type_str == "AVMString" and raw_value:
        return raw_value.decode("utf-8")
    if type_str == "AVMUint64" and raw_value:
        return ABIType.from_string("uint64").decode(raw_value)  # type: ignore[no-any-return]

    # Handle structs
    if struct and struct in structs:
        return_tuple = return_value.return_value
        return get_abi_struct_from_abi_tuple(return_tuple, structs[struct], structs)

    # Return as-is
    return return_value.return_value  # type: ignore[no-any-return]


def get_abi_encoded_value(value: Any, type_str: str, structs: dict[str, list[StructField]]) -> bytes:  # noqa: ANN401, PLR0911
    if isinstance(value, (bytes | bytearray)):
        return value
    if type_str == "AVMUint64":
        return ABIType.from_string("uint64").encode(value)
    if type_str in ("AVMBytes", "AVMString"):
        if isinstance(value, str):
            return value.encode("utf-8")
        if not isinstance(value, (bytes | bytearray)):
            raise ValueError(f"Expected bytes value for {type_str}, but got {type(value)}")
        return value
    if type_str in structs:
        tuple_type = get_abi_tuple_type_from_abi_struct_definition(structs[type_str], structs)
        if isinstance(value, (list | tuple)):
            return tuple_type.encode(value)  # type: ignore[arg-type]
        else:
            tuple_values = get_abi_tuple_from_abi_struct(value, structs[type_str], structs)
            return tuple_type.encode(tuple_values)
    else:
        abi_type = ABIType.from_string(type_str)
        return abi_type.encode(value)


def get_abi_decoded_value(
    value: bytes | int | str, type_str: str | ABITypeAlias | ABIArgumentType, structs: dict[str, list[StructField]]
) -> ABIValue:
    type_value = str(type_str)

    if type_value == "AVMBytes" or not isinstance(value, bytes):
        return value
    if type_value == "AVMString":
        return value.decode("utf-8")
    if type_value == "AVMUint64":
        return ABIType.from_string("uint64").decode(value)  # type: ignore[no-any-return]
    if type_value in structs:
        tuple_type = get_abi_tuple_type_from_abi_struct_definition(structs[type_value], structs)
        decoded_tuple = tuple_type.decode(value)
        return get_abi_struct_from_abi_tuple(decoded_tuple, structs[type_value], structs)
    return ABIType.from_string(type_value).decode(value)  # type: ignore[no-any-return]


def get_abi_tuple_from_abi_struct(
    struct_value: dict[str, Any],
    struct_fields: list[StructField],
    structs: dict[str, list[StructField]],
) -> list[Any]:
    result = []
    for field in struct_fields:
        key = field.name
        if key not in struct_value:
            raise ValueError(f"Missing value for field '{key}'")
        value = struct_value[key]
        field_type = field.type
        if isinstance(field_type, str):
            if field_type in structs:
                value = get_abi_tuple_from_abi_struct(value, structs[field_type], structs)
        elif isinstance(field_type, list):
            value = get_abi_tuple_from_abi_struct(value, field_type, structs)
        result.append(value)
    return result


def get_abi_tuple_type_from_abi_struct_definition(
    struct_def: list[StructField], structs: dict[str, list[StructField]]
) -> TupleType:
    types = []
    for field in struct_def:
        field_type = field.type
        if isinstance(field_type, str):
            if field_type in structs:
                types.append(get_abi_tuple_type_from_abi_struct_definition(structs[field_type], structs))
            else:
                types.append(ABIType.from_string(field_type))  # type: ignore[arg-type]
        elif isinstance(field_type, list):
            types.append(get_abi_tuple_type_from_abi_struct_definition(field_type, structs))
        else:
            raise ValueError(f"Invalid field type: {field_type}")
    return TupleType(types)


def get_abi_struct_from_abi_tuple(
    decoded_tuple: Any,  # noqa: ANN401
    struct_fields: list[StructField],
    structs: dict[str, list[StructField]],
) -> dict[str, Any]:
    result = {}
    for i, field in enumerate(struct_fields):
        key = field.name
        field_type = field.type
        value = decoded_tuple[i]
        if isinstance(field_type, str):
            if field_type in structs:
                value = get_abi_struct_from_abi_tuple(value, structs[field_type], structs)
        elif isinstance(field_type, list):
            value = get_abi_struct_from_abi_tuple(value, field_type, structs)
        result[key] = value
    return result


def arc32_to_arc56(app_spec: ApplicationSpecification) -> Arc56Contract:  # noqa: C901
    """
    Convert ARC-32 application specification to ARC-56 contract format.

    Args:
        app_spec: ARC-32 application specification

    Returns:
        ARC-56 contract specification
    """

    def convert_structs() -> dict[StructName, list[StructField]]:
        structs: dict[StructName, list[StructField]] = {}
        for hint in app_spec.hints.values():
            if not hint.structs:
                continue
            for struct in hint.structs.values():
                fields = [
                    StructField(
                        name=name,
                        type=type_,
                    )
                    for name, type_ in struct["elements"]
                ]
                structs[struct["name"]] = fields
        return structs

    def get_hint(method: AlgorandABIMethod) -> MethodHints | None:
        sig = method.get_signature()
        return app_spec.hints.get(sig)

    def get_default_value(
        type: str | ABIType,
        default_arg: DefaultArgumentDict,
    ) -> DefaultValue | None:
        if not default_arg or default_arg["source"] == "abi-method":
            return None

        source_map = {
            "constant": "literal",
            "global-state": "global",
            "local-state": "local",
        }

        data = default_arg["data"]
        if isinstance(data, str):
            data = base64.b64encode(data.encode()).decode()
        elif isinstance(data, bytes):
            data = base64.b64encode(data).decode()
        else:
            data = str(data)

        return DefaultValue(
            data=data,
            type="AVMString" if type == "string" else str(type),
            source=source_map.get(default_arg["source"], "literal"),  # type: ignore[arg-type]
        )

    def convert_method(method: AlgorandABIMethod) -> Method:
        hint = get_hint(method)

        args: list[MethodArg] = []
        for arg in method.args:
            if not arg.name:
                continue
            struct_name = None
            if hint and hint.structs and arg.name in hint.structs:
                struct_name = hint.structs[arg.name].get("name")

            default_value = None
            if hint and hint.default_arguments and arg.name in hint.default_arguments:
                default_value = get_default_value(str(arg.type), hint.default_arguments[arg.name])

            method_arg = MethodArg(
                type=arg.type,  # type: ignore[arg-type]
                struct=struct_name,
                name=arg.name,
                desc=arg.desc,
                default_value=default_value,
            )
            args.append(method_arg)

        method_returns = MethodReturns(
            type=str(method.returns.type),
            struct=hint.structs.get("output", {}).get("name") if hint and hint.structs else None,  # type: ignore[call-overload]
            desc=method.returns.desc,
        )

        method_actions = MethodActions(
            create=convert_actions(hint.call_config, "CREATE") if hint and hint.call_config else [],  # type: ignore  # noqa: PGH003
            call=convert_actions(hint.call_config, "CALL") if hint and hint.call_config else [],
        )

        return Method(
            name=method.name,
            desc=method.desc,
            args=args,
            returns=method_returns,
            actions=method_actions,
            readonly=hint.read_only if hint else False,
            events=[],
            recommendations=None,
        )

    def convert_storage_keys(schema_dict: AppSpecStateDict) -> dict[str, StorageKey]:
        return {
            name: StorageKey(
                desc=spec.get("descr"),
                key_type=spec["type"],
                value_type="AVMUint64" if spec["type"] == "uint64" else "AVMBytes",
                key=base64.b64encode(spec["key"].encode()).decode(),
            )
            for name, spec in schema_dict.get("declared", {}).items()
        }

    def convert_actions(
        call_config: CallConfig | MethodConfigDict, action_type: Literal["CREATE", "CALL"]
    ) -> list[OnCompleteAction | Literal["NoOp", "OptIn", "DeleteApplication"]]:
        """
        Converts method configuration into a list of on-complete action literals.

        Args:
            call_config (CallConfig | MethodConfigDict): Configuration dictionary or CallConfig object for method actions.
            action_type (Literal["CREATE", "CALL"]): The type of action to convert.

        Returns:
            List[OnCompleteAction]: A list of on-complete action literals.
        """
        config_action_map = {
            "no_op": "NoOp",
            "opt_in": "OptIn",
            "close_out": "CloseOut",
            "clear_state": "ClearState",
            "update_application": "UpdateApplication",
            "delete_application": "DeleteApplication",
        }

        def get_action_value(key: str) -> str | None:
            if isinstance(call_config, dict):
                config_value = call_config.get(key)  # type: ignore[call-overload]
                # Handle legacy CallConfig enum
                return config_value.name if hasattr(config_value, "name") else config_value  # type: ignore[no-any-return]
            # Handle new CallConfig dataclass
            return getattr(call_config, key, None)

        return [action for key, action in config_action_map.items() if get_action_value(key) in ("ALL", action_type)]  # type: ignore  # noqa: PGH003

    # Convert structs
    structs = convert_structs()

    # Get schema information from app_spec
    global_schema = app_spec.schema.get("global", {})
    local_schema = app_spec.schema.get("local", {})

    state = Arc56ContractState(
        schemas={
            "global": {
                "ints": int(app_spec.global_state_schema.num_uints) if app_spec.global_state_schema.num_uints else 0,
                "bytes": int(app_spec.global_state_schema.num_byte_slices)
                if app_spec.global_state_schema.num_byte_slices
                else 0,
            },
            "local": {
                "ints": int(app_spec.local_state_schema.num_uints) if app_spec.local_state_schema.num_uints else 0,
                "bytes": int(app_spec.local_state_schema.num_byte_slices)
                if app_spec.local_state_schema.num_byte_slices
                else 0,
            },
        },
        keys={
            "global": convert_storage_keys(global_schema),
            "local": convert_storage_keys(local_schema),
            "box": {},
        },
        maps={
            "global": {},
            "local": {},
            "box": {},
        },
    )

    contract_source = {
        "approval": app_spec.approval_program,
        "clear": app_spec.clear_program,
    }

    bare_actions = {
        "create": convert_actions(app_spec.bare_call_config, "CREATE"),
        "call": convert_actions(app_spec.bare_call_config, "CALL"),
    }

    return Arc56Contract(
        arcs=[],
        name=app_spec.contract.name,
        desc=app_spec.contract.desc,
        structs=structs,
        methods=[convert_method(m) for m in app_spec.contract.methods],
        state=state,
        source=contract_source,
        bare_actions=bare_actions,
        byte_code=None,
        compiler_info=None,
        events=None,
        networks=None,
        scratch_variables=None,
        source_info=None,
        template_variables=None,
    )
