from algopy import ARC4Contract, String, TemplateVar
from algopy.arc4 import abimethod


class DeleteAbiWithInner(ARC4Contract):
    def __init__(self) -> None:
        self.greeting = TemplateVar[String]("GREETING")

    @abimethod(allow_actions=["DeleteApplication"])
    def delete(self) -> None:
        assert TemplateVar[bool]("DELETABLE")
