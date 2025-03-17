import contextlib
import enum
import os
from dataclasses import dataclass
from typing import overload

import httpx
from typing_extensions import deprecated

from algokit_utils.config import config

__all__ = [
    "DISPENSER_ACCESS_TOKEN_KEY",
    "DISPENSER_ASSETS",
    "DISPENSER_REQUEST_TIMEOUT",
    "DispenserApiConfig",
    "DispenserAsset",
    "DispenserAssetName",
    "DispenserFundResponse",
    "DispenserLimitResponse",
    "TestNetDispenserApiClient",
]


class DispenserApiConfig:
    BASE_URL = "https://api.dispenser.algorandfoundation.tools"


class DispenserAssetName(enum.IntEnum):
    ALGO = 0


@dataclass
class DispenserAsset:
    asset_id: int
    """The ID of the asset"""
    decimals: int
    """The amount of decimal places the asset was created with"""
    description: str
    """The description of the asset"""


@dataclass
class DispenserFundResponse:
    tx_id: str
    """The transaction ID of the funded transaction"""
    amount: int
    """The amount of Algos funded"""


@dataclass
class DispenserLimitResponse:
    amount: int
    """The amount of Algos that can be funded"""


DISPENSER_ASSETS = {
    DispenserAssetName.ALGO: DispenserAsset(
        asset_id=0,
        decimals=6,
        description="Algo",
    ),
}
DISPENSER_REQUEST_TIMEOUT = 15
DISPENSER_ACCESS_TOKEN_KEY = "ALGOKIT_DISPENSER_ACCESS_TOKEN"


class TestNetDispenserApiClient:
    """
    Client for interacting with the [AlgoKit TestNet Dispenser API](https://github.com/algorandfoundation/algokit/blob/main/docs/testnet_api.md).
    To get started create a new access token via `algokit dispenser login --ci`
    and pass it to the client constructor as `auth_token`.
    Alternatively set the access token as environment variable `ALGOKIT_DISPENSER_ACCESS_TOKEN`,
    and it will be auto loaded. If both are set, the constructor argument takes precedence.

    Default request timeout is 15 seconds. Modify by passing `request_timeout` to the constructor.
    """

    # NOTE: ensures pytest does not think this is a test
    # https://docs.pytest.org/en/stable/example/pythoncollection.html#customizing-test-collection
    __test__ = False
    auth_token: str
    request_timeout = DISPENSER_REQUEST_TIMEOUT

    def __init__(self, auth_token: str | None = None, request_timeout: int = DISPENSER_REQUEST_TIMEOUT):
        auth_token_from_env = os.getenv(DISPENSER_ACCESS_TOKEN_KEY)

        if auth_token:
            self.auth_token = auth_token
        elif auth_token_from_env:
            self.auth_token = auth_token_from_env
        else:
            raise Exception(
                f"Can't init AlgoKit TestNet Dispenser API client "
                f"because neither environment variable {DISPENSER_ACCESS_TOKEN_KEY} or "
                "the auth_token were provided."
            )

        self.request_timeout = request_timeout

    def _process_dispenser_request(
        self, *, auth_token: str, url_suffix: str, data: dict | None = None, method: str = "POST"
    ) -> httpx.Response:
        """
        Generalized method to process http requests to dispenser API
        """

        headers = {"Authorization": f"Bearer {(auth_token)}"}

        # Set request arguments
        request_args = {
            "url": f"{DispenserApiConfig.BASE_URL}/{url_suffix}",
            "headers": headers,
            "timeout": self.request_timeout,
        }

        if method.upper() != "GET" and data is not None:
            request_args["json"] = data

        try:
            response: httpx.Response = getattr(httpx, method.lower())(**request_args)
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as err:
            error_message = f"Error processing dispenser API request: {err.response.status_code}"
            error_response = None
            with contextlib.suppress(Exception):
                error_response = err.response.json()

            if error_response and error_response.get("code"):
                error_message = error_response.get("code")

            elif err.response.status_code == httpx.codes.BAD_REQUEST:
                error_message = err.response.json()["message"]

            raise Exception(error_message) from err

        except Exception as err:
            error_message = "Error processing dispenser API request"
            config.logger.debug(f"{error_message}: {err}", exc_info=True)
            raise err

    @overload
    def fund(self, address: str, amount: int) -> DispenserFundResponse: ...

    @overload
    @deprecated("Asset ID parameter is deprecated. Can now use `fund(address, amount)` instead.")
    def fund(self, address: str, amount: int, asset_id: int | None = None) -> DispenserFundResponse: ...

    def fund(self, address: str, amount: int, asset_id: int | None = None) -> DispenserFundResponse:  # noqa: ARG002
        """
        Fund an account with Algos from the dispenser API

        :param address: The address to fund
        :param amount: The amount of Algos to fund
        :param asset_id: The asset ID to fund (deprecated)
        :return: The transaction ID of the funded transaction
        :raises Exception: If the dispenser API request fails

        :example:
            >>> dispenser_client = TestNetDispenserApiClient()
            >>> dispenser_client.fund(address="SENDER_ADDRESS", amount=1000000)
        """

        try:
            response = self._process_dispenser_request(
                auth_token=self.auth_token,
                url_suffix=f"fund/{DISPENSER_ASSETS[DispenserAssetName.ALGO].asset_id}",
                data={
                    "receiver": address,
                    "amount": amount,
                    "assetID": DISPENSER_ASSETS[DispenserAssetName.ALGO].asset_id,
                },
                method="POST",
            )

            content = response.json()
            return DispenserFundResponse(tx_id=content["txID"], amount=content["amount"])

        except Exception as err:
            config.logger.exception(f"Error funding account {address}: {err}")
            raise err

    def refund(self, refund_txn_id: str) -> None:
        """
        Register a refund for a transaction with the dispenser API
        """

        try:
            self._process_dispenser_request(
                auth_token=self.auth_token,
                url_suffix="refund",
                data={"refundTransactionID": refund_txn_id},
                method="POST",
            )

        except Exception as err:
            config.logger.exception(f"Error issuing refund for txn_id {refund_txn_id}: {err}")
            raise err

    def get_limit(
        self,
        address: str,
    ) -> DispenserLimitResponse:
        """
        Get current limit for an account with Algos from the dispenser API
        """

        try:
            response = self._process_dispenser_request(
                auth_token=self.auth_token,
                url_suffix=f"fund/{DISPENSER_ASSETS[DispenserAssetName.ALGO].asset_id}/limit",
                method="GET",
            )
            content = response.json()

            return DispenserLimitResponse(amount=content["amount"])
        except Exception as err:
            config.logger.exception(f"Error setting limit for account {address}: {err}")
            raise err
