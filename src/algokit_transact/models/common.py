from dataclasses import dataclass, field
from enum import Enum


class OnApplicationComplete(Enum):
    NoOp = 0
    OptIn = 1
    CloseOut = 2
    ClearState = 3
    UpdateApplication = 4
    DeleteApplication = 5


@dataclass(slots=True, frozen=True)
class StateSchema:
    num_uints: int = field(default=0, metadata={"kind": "wire", "alias": "nui"})
    num_byte_slices: int = field(default=0, metadata={"kind": "wire", "alias": "nbs"})
