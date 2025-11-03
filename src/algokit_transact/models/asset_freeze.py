from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_transact.codec.serde import addr, wire


@dataclass(slots=True, frozen=True)
class AssetFreezeTransactionFields:
    asset_id: int = field(default=0, metadata=wire("faid"))
    freeze_target: str = field(default=ZERO_ADDRESS, metadata=addr("fadd"))
    frozen: bool = field(default=False, metadata=wire("afrz"))
