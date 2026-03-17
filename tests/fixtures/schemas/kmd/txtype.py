from pydantic import RootModel


class TxTypeSchema(RootModel[str]):
    """TxType is the type of the transaction written to the ledger"""

    pass
