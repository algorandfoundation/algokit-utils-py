import beaker
import pyteal

app = beaker.Application("MultiUnderscoreApp")


@app.external
def some_value(*, output: pyteal.abi.Uint64) -> pyteal.Expr:
    return output.set(pyteal.Tmpl.Int("TMPL_SOME_VALUE"))


@app.update(bare=True, authorize=beaker.Authorize.only_creator())
def update() -> pyteal.Expr:
    return pyteal.Assert(pyteal.Tmpl.Int("TMPL_UPDATABLE"), comment="is updatable")


@app.delete(bare=True, authorize=beaker.Authorize.only_creator())
def delete() -> pyteal.Expr:
    return pyteal.Assert(pyteal.Tmpl.Int("TMPL_DELETABLE"), comment="is deletable")


@app.create(bare=True)
def create() -> pyteal.Expr:
    return pyteal.Approve()
