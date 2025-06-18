from algopy import ARC4Contract, arc4, UInt64, TemplateVar, String


class DeleteAbiWithInner(ARC4Contract):
    def __init__(self) -> None:
        self.greeting = TemplateVar[String]("GREETING")

    @arc4.abimethod(create="require")
    def create(self) -> None:
        return

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete(self, app_id: UInt64) -> None:
        arc4.abi_call("no_op", app_id=app_id)
        assert TemplateVar[bool]("DELETABLE")
