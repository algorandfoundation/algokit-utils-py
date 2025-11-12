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
        metadata=wire("app-index"),
    )
    field_name: str = field(
        metadata=wire("field-name"),
    )
    source: str = field(
        metadata=wire("source"),
    )
    txn_index: int = field(
        metadata=wire("txn-index"),
    )
