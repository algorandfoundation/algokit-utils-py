from typing import Literal

import beaker
import pyteal
from beaker.lib.storage import BoxMapping


class State:
    greeting = beaker.GlobalStateValue(pyteal.TealType.bytes)
    last = beaker.LocalStateValue(pyteal.TealType.bytes, default=pyteal.Bytes("unset"))
    box = BoxMapping(pyteal.abi.StaticBytes[Literal[4]], pyteal.abi.String)


app = beaker.Application("HelloWorldApp", state=State())


@app.external
def version(*, output: pyteal.abi.Uint64) -> pyteal.Expr:
    return output.set(pyteal.Tmpl.Int("TMPL_VERSION"))


@app.external(read_only=True)
def readonly(error: pyteal.abi.Uint64) -> pyteal.Expr:
    return pyteal.If(error.get(), pyteal.Assert(pyteal.Int(0), comment="An error"), pyteal.Approve())


@app.external()
def set_box(name: pyteal.abi.StaticBytes[Literal[4]], value: pyteal.abi.String) -> pyteal.Expr:
    return app.state.box[name.get()].set(value.get())


@app.external
def get_box(name: pyteal.abi.StaticBytes[Literal[4]], *, output: pyteal.abi.String) -> pyteal.Expr:
    return output.set(app.state.box[name.get()].get())


@app.external(read_only=True)
def get_box_readonly(name: pyteal.abi.StaticBytes[Literal[4]], *, output: pyteal.abi.String) -> pyteal.Expr:
    return output.set(app.state.box[name.get()].get())


@app.update(authorize=beaker.Authorize.only_creator())
def update() -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Tmpl.Int("TMPL_UPDATABLE"), comment="is updatable"),
        app.state.greeting.set(pyteal.Bytes("Updated ABI")),
    )


@app.update(bare=True, authorize=beaker.Authorize.only_creator())
def update_bare() -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Tmpl.Int("TMPL_UPDATABLE"), comment="is updatable"),
        app.state.greeting.set(pyteal.Bytes("Updated Bare")),
    )


@app.update(authorize=beaker.Authorize.only_creator())
def update_args(check: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Eq(check.get(), pyteal.Bytes("Yes")), comment="passes update check"),
        pyteal.Assert(pyteal.Tmpl.Int("TMPL_UPDATABLE"), comment="is updatable"),
        app.state.greeting.set(pyteal.Bytes("Updated Args")),
    )


@app.delete(authorize=beaker.Authorize.only_creator())
def delete() -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Tmpl.Int("TMPL_DELETABLE"), comment="is deletable"),
    )


@app.delete(bare=True, authorize=beaker.Authorize.only_creator())
def delete_bare() -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Tmpl.Int("TMPL_DELETABLE"), comment="is deletable"),
    )


@app.delete(authorize=beaker.Authorize.only_creator())
def delete_args(check: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Eq(check.get(), pyteal.Bytes("Yes")), comment="passes delete check"),
        pyteal.Assert(pyteal.Tmpl.Int("TMPL_DELETABLE"), comment="is deletable"),
    )


@app.external(method_config={"opt_in": pyteal.CallConfig.CREATE})
def create_opt_in() -> pyteal.Expr:
    return pyteal.Seq(
        app.state.greeting.set(pyteal.Bytes("Opt In")),
        pyteal.Approve(),
    )


@app.external
def update_greeting(greeting: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(
        app.state.greeting.set(greeting.get()),
    )


@app.create(bare=True)
def create_bare() -> pyteal.Expr:
    return pyteal.Seq(
        app.state.greeting.set(pyteal.Bytes("Hello Bare")),
        pyteal.Approve(),
    )


@app.create
def create() -> pyteal.Expr:
    return pyteal.Seq(
        app.state.greeting.set(pyteal.Bytes("Hello ABI")),
        pyteal.Approve(),
    )


@app.create
def create_args(greeting: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(
        app.state.greeting.set(greeting.get()),
        pyteal.Approve(),
    )


@app.external(read_only=True)
def hello(name: pyteal.abi.String, *, output: pyteal.abi.String) -> pyteal.Expr:
    return output.set(pyteal.Concat(app.state.greeting, pyteal.Bytes(", "), name.get()))


@app.external
def hello_remember(name: pyteal.abi.String, *, output: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(
        app.state.last.set(name.get()), output.set(pyteal.Concat(app.state.greeting, pyteal.Bytes(", "), name.get()))
    )


@app.external(read_only=True)
def get_last(*, output: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(output.set(app.state.last.get()))


@app.clear_state
def clear_state() -> pyteal.Expr:
    return pyteal.Approve()


@app.opt_in
def opt_in() -> pyteal.Expr:
    return pyteal.Seq(
        app.state.last.set(pyteal.Bytes("Opt In ABI")),
        pyteal.Approve(),
    )


@app.opt_in(bare=True)
def opt_in_bare() -> pyteal.Expr:
    return pyteal.Seq(
        app.state.last.set(pyteal.Bytes("Opt In Bare")),
        pyteal.Approve(),
    )


@app.opt_in
def opt_in_args(check: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Eq(check.get(), pyteal.Bytes("Yes")), comment="passes opt_in check"),
        app.state.last.set(pyteal.Bytes("Opt In Args")),
        pyteal.Approve(),
    )


@app.close_out
def close_out() -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Approve(),
    )


@app.close_out(bare=True)
def close_out_bare() -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Approve(),
    )


@app.close_out
def close_out_args(check: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(
        pyteal.Assert(pyteal.Eq(check.get(), pyteal.Bytes("Yes")), comment="passes close_out check"),
        pyteal.Approve(),
    )


@app.external
def call_with_payment(payment: pyteal.abi.PaymentTransaction, *, output: pyteal.abi.String) -> pyteal.Expr:
    return pyteal.Seq(pyteal.Assert(payment.get().amount() > pyteal.Int(0)), output.set("Payment Successful"))
