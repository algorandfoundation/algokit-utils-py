from typing import Literal

from algopy import Application, ARC4Contract, Box, BoxMap, Bytes, arc4, op


class DummyStruct(arc4.Struct):
    name: arc4.String
    id: arc4.UInt64


class External(ARC4Contract):
    def __init__(self) -> None:
        self.box = Box(Bytes)

    @arc4.abimethod
    def set_box(self) -> None:
        self.box.value = Bytes(b"foo")


class TestPuyaBoxes(ARC4Contract):
    def __init__(self) -> None:
        self.box_bytes = BoxMap(arc4.String, Bytes)
        self.box_bytes2 = BoxMap(Bytes, Bytes)
        self.box_str = BoxMap(arc4.String, arc4.String)
        self.box_int = BoxMap(arc4.String, arc4.UInt32)
        self.box_int512 = BoxMap(arc4.String, arc4.UInt512)
        self.box_static = BoxMap(arc4.String, arc4.StaticArray[arc4.Byte, Literal[4]])
        self.external = Application(0)

    @arc4.abimethod
    def set_box_bytes(self, name: arc4.String, value: Bytes) -> None:
        self.box_bytes[name] = value

    @arc4.abimethod
    def set_box_str(self, name: arc4.String, value: arc4.String) -> None:
        self.box_str[name] = value

    @arc4.abimethod
    def set_box_int(self, name: arc4.String, value: arc4.UInt32) -> None:
        self.box_int[name] = value

    @arc4.abimethod
    def set_box_int512(self, name: arc4.String, value: arc4.UInt512) -> None:
        self.box_int512[name] = value

    @arc4.abimethod
    def set_box_static(self, name: arc4.String, value: arc4.StaticArray[arc4.Byte, Literal[4]]) -> None:
        self.box_static[name] = value.copy()

    @arc4.abimethod()
    def set_struct(self, name: arc4.String, value: DummyStruct) -> None:
        assert name.bytes == value.name.bytes, "Name must match id of struct"
        op.Box.put(name.bytes, value.bytes)

    @arc4.abimethod
    def bootstrap_external_app(self) -> Application:
        self.external = arc4.arc4_create(External).created_app
        return self.external

    @arc4.abimethod
    def set_external_box(self) -> None:
        arc4.abi_call(
            External.set_box,
            app_id=self.external,
        )
