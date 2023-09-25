import contextlib
import enum
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


class DispenserApiConfig:
    BASE_URL = "https://api.dispenser.algorandfoundation.tools"


class DispenserApiErrorCode:
    DISPENSER_OUT_OF_FUNDS = "dispenser_out_of_funds"
    FORBIDDEN = "forbidden"
    FUND_LIMIT_EXCEEDED = "fund_limit_exceeded"
    DISPENSER_ERROR = "dispenser_error"
    MISSING_PARAMETERS = "missing_params"
    AUTHORIZATION_ERROR = "authorization_error"
    REPUTATION_REFRESH_FAILED = "reputation_refresh_failed"
    TXN_EXPIRED = "txn_expired"
    TXN_INVALID = "txn_invalid"
    TXN_ALREADY_PROCESSED = "txn_already_processed"
    INVALID_ASSET = "invalid_asset"
    UNEXPECTED_ERROR = "unexpected_error"


class DispenserAssetName(enum.IntEnum):
    ALGO = 0


@dataclass
class DispenserAsset:
    asset_id: int
    decimals: int
    description: str


DISPENSER_ASSETS = {
    DispenserAssetName.ALGO: DispenserAsset(
        asset_id=0,
        decimals=6,
        description="Algo",
    ),
}
DISPENSER_REQUEST_TIMEOUT = 15
DISPENSER_ACCESS_TOKEN_KEY = "ALGOKIT_DISPENSER_ACCESS_TOKEN"


def _get_hours_until_reset(resets_at: str) -> float:
    now_utc = datetime.now(timezone.utc)
    reset_date = datetime.strptime(resets_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    return round((reset_date - now_utc).total_seconds() / 3600, 1)


def _process_dispenser_request(
    *, auth_token: str, url_suffix: str, data: dict | None = None, method: str = "POST"
) -> httpx.Response:
    """
    Generalized method to process http requests to dispenser API
    """

    headers = {"Authorization": f"Bearer {(auth_token)}"}

    # Set request arguments
    request_args = {
        "url": f"{DispenserApiConfig.BASE_URL}/{url_suffix}",
        "headers": headers,
        "timeout": DISPENSER_REQUEST_TIMEOUT,
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

        if error_response and error_response.get("code") == DispenserApiErrorCode.FUND_LIMIT_EXCEEDED:
            hours_until_reset = _get_hours_until_reset(error_response.get("resetsAt"))
            error_message = (
                "Limit exceeded. "
                f"Try again in ~{hours_until_reset} hours if your request doesn't exceed the daily limit."
            )

        elif err.response.status_code == httpx.codes.BAD_REQUEST:
            error_message = err.response.json()["message"]

        raise Exception(error_message) from err

    except Exception as err:
        error_message = "Error processing dispenser API request"
        logger.debug(f"{error_message}: {err}", exc_info=True)
        raise err


def process_dispenser_fund_request(address: str, amount: int, asset_id: int, auth_token: str) -> str:
    """
    Fund an account with Algos from the dispenser API
    """
    try:
        response = _process_dispenser_request(
            auth_token=auth_token,
            url_suffix=f"fund/{asset_id}",
            data={"receiver": address, "amount": amount, "assetID": asset_id},
            method="POST",
        )
        content = response.json()

        return str(content["txID"])
    except Exception as err:
        logger.error(f"Error funding account {address}: {err}")
        raise err
