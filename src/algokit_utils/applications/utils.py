from base64 import b64encode
from typing import Any, Literal, cast

import algosdk
from algosdk.abi import Method

from algokit_utils._legacy_v2.application_specification import (
    ApplicationSpecification,
    CallConfig,
    DefaultArgumentDict,
    MethodConfigDict,
    MethodHints,
    OnCompleteActionName,
)
from algokit_utils.models.application import (
    Arc56Contract,
    Arc56Method,
    Arc56MethodArg,
    Arc56State,
    StorageKey,
)


def arc32_to_arc56(app_spec: ApplicationSpecification) -> Arc56Contract:  # noqa: C901
    """
    Convert ARC-32 application specification to ARC-56 contract format.

    Args:
        app_spec: ARC-32 application specification

    Returns:
        ARC-56 contract specification
    """

    def convert_structs() -> dict[str, list[dict[str, str]]]:
        structs = {}
        for hint in app_spec.hints.values():
            if not hint.structs:
                continue
            for struct in hint.structs.values():
                fields = [{"name": name, "type": type_} for name, type_ in struct["elements"]]
                structs[struct["name"]] = fields
        return structs

    def get_hint(method: Method) -> MethodHints | None:
        sig = method.get_signature()
        return app_spec.hints.get(sig)

    def convert_actions(call_config: MethodConfigDict, action_type: Literal["CREATE", "CALL"]) -> list[str]:
        actions: list[str] = []
        action_map: dict[OnCompleteActionName, str] = {
            "close_out": "CloseOut",
            "delete_application": "DeleteApplication",
            "no_op": "NoOp",
            "opt_in": "OptIn",
            "update_application": "UpdateApplication",
        }

        for config_key, action_name in action_map.items():
            config_value = call_config.get(config_key, CallConfig.NEVER)
            if (
                config_value == CallConfig.ALL
                or (config_value == CallConfig.CREATE and action_type == "CREATE")
                or (config_value == CallConfig.CALL and action_type == "CALL")
            ):
                actions.append(action_name)

        return actions

    def get_default_value(
        type_: str | algosdk.abi.ABIType, default_arg: DefaultArgumentDict
    ) -> dict[str, str | int] | None:
        if not default_arg or default_arg["source"] == "abi-method":
            return None

        source_map = {"constant": "literal", "global-state": "global", "local-state": "local"}

        data = default_arg["data"]
        if isinstance(data, str):
            data = b64encode(data.encode()).decode()

        return cast(
            dict[str, str | int],
            {
                "source": source_map[default_arg["source"]],
                "data": data,
                "type": "AVMString" if type_ == "string" else str(type_),
            },
        )

    def convert_method(method: Method) -> Arc56Method:
        hint = get_hint(method)

        args: list[Arc56MethodArg] = []
        for arg in method.args:
            if not arg.name:
                continue
            struct_name = None
            if hint and hint.structs and arg.name in hint.structs:
                struct_name = hint.structs[arg.name].get("name")

            default_value = None
            if hint and hint.default_arguments and arg.name in hint.default_arguments:
                default_value = get_default_value(arg.type, hint.default_arguments[arg.name])

            args.append(
                cast(
                    Arc56MethodArg,
                    {
                        "name": arg.name,
                        "type": arg.type,
                        "desc": arg.desc,
                        "struct": struct_name,
                        "defaultValue": default_value,
                    },
                )
            )

        return {
            "name": method.name,
            "desc": method.desc,
            "args": args,
            "returns": {
                "type": method.returns.type,
                "desc": method.returns.desc,
                "struct": hint.structs.get("output", {}).get("name")  # type: ignore[call-overload]
                if hint and hint.structs
                else None,
            },
            "events": [],
            "readonly": hint.read_only if hint else None,
            "actions": {
                "create": convert_actions(hint.call_config, "CREATE") if hint and hint.call_config else [],
                "call": convert_actions(hint.call_config, "CALL") if hint and hint.call_config else [],
            },
        }

    def convert_storage_keys(schema_dict: dict[str, Any]) -> dict[str, StorageKey]:
        return {
            name: cast(
                StorageKey,
                {
                    "key": b64encode(spec["key"].encode()).decode(),
                    "keyType": "AVMString",
                    "valueType": "AVMUint64" if spec["type"] == "uint64" else "AVMBytes",
                    "desc": spec.get("descr"),
                },
            )
            for name, spec in schema_dict["declared"].items()
        }

    # Get schema information from app_spec
    global_schema = app_spec.schema.get("global", {})
    local_schema = app_spec.schema.get("local", {})

    # TODO: remove cast
    state: Arc56State = cast(
        Arc56State,
        {
            "schema": {
                "global": {
                    "ints": app_spec.global_state_schema.num_uints,
                    "bytes": app_spec.global_state_schema.num_byte_slices,
                },
                "local": {
                    "ints": app_spec.local_state_schema.num_uints,
                    "bytes": app_spec.local_state_schema.num_byte_slices,
                },
            },
            "keys": {
                "global": convert_storage_keys(global_schema),
                "local": convert_storage_keys(local_schema),
                "box": {},
            },
            "maps": {"global": {}, "local": {}, "box": {}},
        },
    )

    bare_actions = cast(
        dict[Literal["create", "call"], list[str]],
        {
            "create": convert_actions(app_spec.bare_call_config, "CREATE"),
            "call": convert_actions(app_spec.bare_call_config, "CALL"),
        },
    )

    return Arc56Contract(
        arcs=[],
        name=app_spec.contract.name,
        desc=app_spec.contract.desc,
        structs=convert_structs(),
        methods=[convert_method(m) for m in app_spec.contract.methods],
        state=state,
        source={"approval": app_spec.approval_program, "clear": app_spec.clear_program},
        bareActions=bare_actions,
        byteCode=None,
        compilerInfo=None,
        events=None,
        networks=None,
        scratchVariables=None,
        sourceInfo=None,
        templateVariables=None,
    )
