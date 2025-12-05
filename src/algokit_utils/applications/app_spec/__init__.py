# app spec definitions used to be defined here, import new definitions from algokit_abi for backwards compatability
from algokit_abi import arc32, arc56
from algokit_abi.arc32 import Arc32Contract
from algokit_abi.arc56 import Arc56Contract

__all__ = ["Arc32Contract", "Arc56Contract", "arc32", "arc56"]
