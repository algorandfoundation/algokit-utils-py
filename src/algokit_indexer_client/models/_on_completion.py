# AUTO-GENERATED: oas_generator


from enum import Enum


class OnCompletion(Enum):
    r"""
    \[apan\] defines the what additional actions occur with the transaction.

    Valid types:
    * noop
    * optin
    * closeout
    * clear
    * update
    * delete
    """

    NOOP = "noop"
    OPTIN = "optin"
    CLOSEOUT = "closeout"
    CLEAR = "clear"
    UPDATE = "update"
    DELETE = "delete"
