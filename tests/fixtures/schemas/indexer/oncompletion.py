from pydantic import RootModel


class OnCompletionSchema(RootModel[str]):
    """\[apan\] defines the what additional actions occur with the transaction.

    Valid types:
    * noop
    * optin
    * closeout
    * clear
    * update
    * delete"""

    pass
