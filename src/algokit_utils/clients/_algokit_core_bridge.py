import base64
from collections.abc import Iterable

from algosdk.encoding import msgpack_encode
from algosdk.transaction import GenericSignedTransaction
from algosdk.v2client.algod import AlgodClient

from algokit_utils import _EXPERIMENTAL_DEPENDENCIES_INSTALLED

if not _EXPERIMENTAL_DEPENDENCIES_INSTALLED:
    raise ImportError(
        "Installing experimental dependencies is necessary to use AlgodClientWithCore. "
        "Install this package with --group=experimental"
    )

import algokit_algod_api


class AlgodClientWithCore:
    """
    A decorator for AlgodClient that extends its functionality with algokit_algod_api capabilities.
    This class wraps an AlgodClient instance while maintaining the same interface.
    """

    def __init__(self, algod_client: AlgodClient):
        self._algod_client = algod_client

        configuration = algokit_algod_api.Configuration(
            host=algod_client.algod_address, api_key={"api_key": self._algod_client.algod_token}
        )
        api_client = algokit_algod_api.ApiClient(configuration)
        self._algod_core_client = algokit_algod_api.AlgodApi(api_client=api_client)

    def send_raw_transaction(self, txn):
        """
        Override the method to send a raw transaction using algokit_algod_api.
        """
        return self._algod_core_client.raw_transaction(base64.b64decode(txn))

    def send_transactions(self, txns: Iterable[GenericSignedTransaction]):
        """
        Override the method to send multiple transactions using algokit_algod_api.
        """
        return self.send_raw_transaction(
            base64.b64encode(b"".join(base64.b64decode(msgpack_encode(txn)) for txn in txns))
        )

    def __getattr__(self, name):
        """
        Delegate all other method calls to the wrapped AlgodClient instance.
        """
        return getattr(self._algod_client, name)
