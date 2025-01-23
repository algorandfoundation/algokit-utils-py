"""
This module contains common classes and methods that are reused in more than one file.
"""

import base64
import typing

from algosdk.source_map import SourceMap

from algokit_utils._legacy_v2.deploy import strip_comments

if typing.TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


class Program:
    """A compiled TEAL program

    :param program: The TEAL program source code
    :param client: The AlgodClient instance to use for compiling the program
    """

    def __init__(self, program: str, client: "AlgodClient"):
        self.teal = program
        result: dict = client.compile(strip_comments(self.teal), source_map=True)
        self.raw_binary = base64.b64decode(result["result"])
        self.binary_hash: str = result["hash"]
        self.source_map = SourceMap(result["sourcemap"])
