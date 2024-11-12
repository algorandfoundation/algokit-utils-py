import base64
from typing import TYPE_CHECKING, Literal, Union

from algosdk.abi import Method as AlgorandABIMethod

from algokit_utils._legacy_v2.application_specification import (
    ApplicationSpecification,
    AppSpecStateDict,
    DefaultArgumentDict,
    MethodConfigDict,
    MethodHints,
)
from algokit_utils.models.abi import ABIValue
from algokit_utils.models.application import (
    Arc56Contract,
    Arc56ContractState,
    ARCType,
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

if TYPE_CHECKING:
    import algosdk

from typing import Any

from algosdk.abi import ABIType, TupleType


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


def get_abi_decoded_value(value: bytes | int | str, type_str: str, structs: dict[str, list[StructField]]) -> ABIValue:
    if type_str == "AVMBytes" or not isinstance(value, bytes):
        return value
    if type_str == "AVMString":
        return value.decode("utf-8")
    if type_str == "AVMUint64":
        return ABIType.from_string("uint64").decode(value)  # type: ignore[no-any-return]
    if type_str in structs:
        tuple_type = get_abi_tuple_type_from_abi_struct_definition(structs[type_str], structs)
        decoded_tuple = tuple_type.decode(value)
        return get_abi_struct_from_abi_tuple(decoded_tuple, structs[type_str], structs)
    return ABIType.from_string(type_str).decode(value)  # type: ignore[no-any-return]


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
        field_type = field.type_
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
        field_type = field.type_
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
        field_type = field.type_
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
                        type_=type_,
                    )
                    for name, type_ in struct["elements"]
                ]
                structs[struct["name"]] = fields
        return structs

    def get_hint(method: AlgorandABIMethod) -> MethodHints | None:
        sig = method.get_signature()
        return app_spec.hints.get(sig)

    def get_default_value(
        type_: Union[str, "algosdk.abi.ABIType"],
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
            type_="AVMString" if type_ == "string" else str(type_),
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
                type_=str(arg.type),
                struct=struct_name,
                name=arg.name,
                desc=arg.desc,
                default_value=default_value,
            )
            args.append(method_arg)

        method_returns = MethodReturns(
            type_=str(method.returns.type),
            struct=hint.structs.get("output", {}).get("name") if hint and hint.structs else None,  # type: ignore[call-overload]
            desc=method.returns.desc,
        )

        method_actions = MethodActions(
            create=convert_actions(hint.call_config, "CREATE") if hint and hint.call_config else [],  # type: ignore[arg-type]
            call=convert_actions(hint.call_config, "CALL") if hint and hint.call_config else [],  # type: ignore[arg-type]
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
            call_config (MethodConfigDict): Configuration dictionary for method actions.
            action_type (Literal["CREATE", "CALL"]): The type of action to convert.

        Returns:
            List[Literal['NoOp', 'OptIn', 'DeleteApplication']]: A list of on-complete action literals.
        """

        config_action_map: dict[str, OnCompleteAction] = {
            "no_op": "NoOp",
            "opt_in": "OptIn",
            "close_out": "CloseOut",
            "clear_state": "ClearState",
            "update_application": "UpdateApplication",
            "delete_application": "DeleteApplication",
        }

        return [
            action
            for key, action in config_action_map.items()
            if hasattr(call_config, key) and getattr(call_config, key) in ("ALL", action_type)
        ]

    # Convert structs
    structs = convert_structs()

    # Get schema information from app_spec
    global_schema = app_spec.schema.get("global", {})
    local_schema = app_spec.schema.get("local", {})

    state = Arc56ContractState(
        schemas={
            "global": {
                "ints": app_spec.global_state_schema.num_uints,  # type: ignore[attr-defined]
                "bytes": app_spec.global_state_schema.num_byte_slices,  # type: ignore[attr-defined]
            },
            "local": {
                "ints": app_spec.local_state_schema.num_uints,  # type: ignore[attr-defined]
                "bytes": app_spec.local_state_schema.num_byte_slices,  # type: ignore[attr-defined]
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
        arcs=[ARCType.ARC56],
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
