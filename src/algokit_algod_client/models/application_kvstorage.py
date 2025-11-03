# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .avm_key_value import AvmKeyValue


@dataclass(slots=True)
class ApplicationKvstorage:
    """
    An application's global/local/box state.
    """

    kvs: list[AvmKeyValue] = field(
        metadata=wire(
            "kvs",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AvmKeyValue, raw),
        ),
    )
    account: str | None = field(
        default=None,
        metadata=wire("account"),
    )
