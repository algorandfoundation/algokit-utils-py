# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class DryrunSource:
    """
    DryrunSource is TEAL source text that gets uploaded, compiled, and inserted into
    transactions or application state.
    """

    app_id: int = field(
        default=0,
        metadata=wire("app-index"),
    )
    field_name: str = field(
        default="",
        metadata=wire("field-name"),
    )
    source: str = field(
        default="",
        metadata=wire("source"),
    )
    txn_index: int = field(
        default=0,
        metadata=wire("txn-index"),
    )
