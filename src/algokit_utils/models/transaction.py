from typing import Any, Literal, TypedDict

__all__ = [
    "Arc2TransactionNote",
    "BaseArc2Note",
    "JsonFormatArc2Note",
    "SendParams",
    "StringFormatArc2Note",
    "TransactionNote",
    "TransactionNoteData",
]


# Define specific types for different formats
class BaseArc2Note(TypedDict):
    """Base ARC-0002 transaction note structure"""

    dapp_name: str


class StringFormatArc2Note(BaseArc2Note):
    """ARC-0002 note for string-based formats (m/b/u)"""

    format: Literal["m", "b", "u"]
    data: str


class JsonFormatArc2Note(BaseArc2Note):
    """ARC-0002 note for JSON format"""

    format: Literal["j"]
    data: str | dict[str, Any] | list[Any] | int | None


# Combined type for all valid ARC-0002 notes
# See: https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md
Arc2TransactionNote = StringFormatArc2Note | JsonFormatArc2Note

TransactionNoteData = str | None | int | list[Any] | dict[str, Any]
TransactionNote = bytes | TransactionNoteData | Arc2TransactionNote


class SendParams(TypedDict, total=False):
    """Parameters for sending a transaction"""

    max_rounds_to_wait: int
    suppress_log: bool
    populate_app_call_resources: bool
    cover_app_call_inner_transaction_fees: bool
