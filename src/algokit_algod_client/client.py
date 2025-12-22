# AUTO-GENERATED: oas_generator
import random
import time
from base64 import b64encode
from collections.abc import Sequence
from dataclasses import is_dataclass
from typing import Any, Literal, TypeVar, overload

import httpx
import msgpack

from algokit_common.serde import from_wire, to_wire

from . import models
from .config import ClientConfig
from .exceptions import UnexpectedStatusError
from .types import Headers

# HTTP status codes that warrant a retry (aligned with algokit-utils-ts)
_RETRY_STATUS_CODES: frozenset[int] = frozenset({408, 413, 429, 500, 502, 503, 504})
# Network error codes that warrant a retry (aligned with algokit-utils-ts)
_RETRY_ERROR_CODES: frozenset[str] = frozenset(
    {
        "ETIMEDOUT",
        "ECONNRESET",
        "EADDRINUSE",
        "ECONNREFUSED",
        "EPIPE",
        "ENOTFOUND",
        "ENETUNREACH",
        "EAI_AGAIN",
        "EPROTO",
    }
)
_MAX_BACKOFF_MS: float = 10_000.0
_DEFAULT_MAX_TRIES: int = 5

ModelT = TypeVar("ModelT")
ListModelT = TypeVar("ListModelT")
PrimitiveT = TypeVar("PrimitiveT")

# Prefixed markers used when converting unhashable msgpack map keys into hashable tuples
_UNHASHABLE_PREFIXES: dict[str, str] = {
    "dict": "__dict_key__",
    "list": "__list_key__",
    "set": "__set_key__",
    "generic": "__unhashable__",
}


class AlgodClient:
    def __init__(self, config: ClientConfig | None = None, *, http_client: httpx.Client | None = None) -> None:
        self._config = config or ClientConfig()
        # Track whether a custom HTTP client was provided to avoid retry conflicts
        self._uses_custom_client = http_client is not None
        self._client = http_client or httpx.Client(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            verify=self._config.verify,
        )

    def close(self) -> None:
        self._client.close()

    def _calculate_max_tries(self) -> int:
        """Calculate maximum number of tries from config.max_retries."""
        max_retries = self._config.max_retries
        if not isinstance(max_retries, int) or max_retries < 0:
            return _DEFAULT_MAX_TRIES
        return max_retries + 1

    def _should_retry(self, error: Exception | None, status_code: int | None, attempt: int, max_tries: int) -> bool:
        """Determine if a request should be retried based on error/status and attempt count."""
        if attempt >= max_tries:
            return False

        # Check HTTP status code
        if status_code is not None and status_code in _RETRY_STATUS_CODES:
            return True

        # Check network error codes (aligned with algokit-utils-ts)
        if error is not None:
            error_code = self._extract_error_code(error)
            if error_code and error_code in _RETRY_ERROR_CODES:
                return True

        return False

    def _extract_error_code(self, error: BaseException) -> str | None:
        """Extract error code from exception, checking common attributes."""
        # Check for 'code' attribute (common in OS/network errors)
        if hasattr(error, "code") and isinstance(error.code, str):
            return error.code
        # Check for errno attribute
        if hasattr(error, "errno") and error.errno is not None:
            import errno as errno_module

            try:
                return errno_module.errorcode.get(error.errno)
            except (TypeError, AttributeError):
                pass
        # Check __cause__ for wrapped errors
        if error.__cause__ is not None:
            return self._extract_error_code(error.__cause__)
        return None

    def _request_with_retry(self, request_kwargs: dict[str, Any]) -> httpx.Response:
        """Execute request with exponential backoff retry for transient failures.

        When a custom HTTP client is provided, retries are disabled to avoid
        conflicts with any retry mechanism the custom client may implement.
        """
        # Disable retries when using a custom HTTP client to avoid conflicts
        # with the client's own retry mechanism
        if self._uses_custom_client:
            return self._client.request(**request_kwargs)

        max_tries = self._calculate_max_tries()
        attempt = 1
        last_error: Exception | None = None

        while attempt <= max_tries:
            status_code: int | None = None
            try:
                response = self._client.request(**request_kwargs)
                status_code = response.status_code
                if not self._should_retry(None, status_code, attempt, max_tries):
                    return response
            except httpx.TransportError as exc:
                last_error = exc
                if not self._should_retry(exc, None, attempt, max_tries):
                    raise

            if attempt == 1:
                backoff_ms = 0.0
            else:
                base_backoff = min(1000.0 * (2 ** (attempt - 1)), _MAX_BACKOFF_MS)
                jitter = 0.5 + random.random()  # Random value between 0.5 and 1.5
                backoff_ms = base_backoff * jitter
            if backoff_ms > 0:
                time.sleep(backoff_ms / 1000.0)
            attempt += 1

        # Should not reach here, but satisfy type checker
        if last_error:
            raise last_error
        raise RuntimeError(f"Request failed after {max_tries} attempt(s)")

    # public

    def _application_box_by_name(
        self,
        application_id: int,
        name: str,
    ) -> models.Box:
        """
        Get box information for a given application.
        """

        path = "/v2/applications/{application-id}/box"
        path = path.replace("{application-id}", str(application_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if name is not None:
            params["name"] = name

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Box)

        raise UnexpectedStatusError(response.status_code, response.text)

    def _raw_transaction(
        self,
        body: bytes,
    ) -> models.PostTransactionsResponse:
        """
        Broadcasts a raw transaction or transaction group to the network.
        """

        path = "/v2/transactions"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/x-binary"]

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "is_binary": True,
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostTransactionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def _transaction_params(
        self,
    ) -> models.TransactionParametersResponse:
        """
        Get parameters for constructing a new transaction
        """

        path = "/v2/transactions/params"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TransactionParametersResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def account_application_information(
        self,
        address: str,
        application_id: int,
        *,
        response_format: Literal["json", "msgpack"] | None = None,
    ) -> models.AccountApplicationResponse:
        """
        Get account information about a given app.
        """

        path = "/v2/accounts/{address}/applications/{application-id}"
        path = path.replace("{address}", str(address))

        path = path.replace("{application-id}", str(application_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        selected_format = response_format

        if selected_format == "msgpack":
            params["format"] = "msgpack"
            accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.AccountApplicationResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def account_asset_information(
        self,
        address: str,
        asset_id: int,
    ) -> models.AccountAssetResponse:
        """
        Get account information about a given asset.
        """

        path = "/v2/accounts/{address}/assets/{asset-id}"
        path = path.replace("{address}", str(address))

        path = path.replace("{asset-id}", str(asset_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.AccountAssetResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def account_information(
        self,
        address: str,
        *,
        exclude: str | None = None,
    ) -> models.Account:
        """
        Get account information.
        """

        path = "/v2/accounts/{address}"
        path = path.replace("{address}", str(address))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if exclude is not None:
            params["exclude"] = exclude

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Account)

        raise UnexpectedStatusError(response.status_code, response.text)

    def application_boxes(
        self,
        application_id: int,
        *,
        max_: int | None = None,
    ) -> models.BoxesResponse:
        """
        Get all box names for a given application.
        """

        path = "/v2/applications/{application-id}/boxes"
        path = path.replace("{application-id}", str(application_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if max_ is not None:
            params["max"] = max_

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.BoxesResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def application_by_id(
        self,
        application_id: int,
    ) -> models.Application:
        """
        Get application information.
        """

        path = "/v2/applications/{application-id}"
        path = path.replace("{application-id}", str(application_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Application)

        raise UnexpectedStatusError(response.status_code, response.text)

    def asset_by_id(
        self,
        asset_id: int,
    ) -> models.Asset:
        """
        Get asset information.
        """

        path = "/v2/assets/{asset-id}"
        path = path.replace("{asset-id}", str(asset_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Asset)

        raise UnexpectedStatusError(response.status_code, response.text)

    def block(
        self,
        round_: int,
        *,
        header_only: bool | None = None,
    ) -> models.BlockResponse:
        """
        Get the block for the given round.
        """

        path = "/v2/blocks/{round}"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if header_only is not None:
            params["header-only"] = header_only

        accept_value: str | None = None

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.BlockResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def block_hash(
        self,
        round_: int,
    ) -> models.BlockHashResponse:
        """
        Get the block hash for the block on the given round.
        """

        path = "/v2/blocks/{round}/hash"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.BlockHashResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def block_time_stamp_offset(
        self,
    ) -> models.GetBlockTimeStampOffsetResponse:
        """
        Returns the timestamp offset. Timestamp offsets can only be set in dev mode.
        """

        path = "/v2/devmode/blocks/offset"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetBlockTimeStampOffsetResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def block_tx_ids(
        self,
        round_: int,
    ) -> models.BlockTxidsResponse:
        """
        Get the top level transaction IDs for the block on the given round.
        """

        path = "/v2/blocks/{round}/txids"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.BlockTxidsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def genesis(
        self,
    ) -> models.GenesisFileInJson:
        """
        Gets the genesis information.
        """

        path = "/genesis"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GenesisFileInJson)

        raise UnexpectedStatusError(response.status_code, response.text)

    def health_check(
        self,
    ) -> None:
        """
        Returns OK if healthy.
        """

        path = "/health"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def ledger_state_delta(
        self,
        round_: int,
    ) -> models.LedgerStateDelta:
        """
        Get a LedgerStateDelta object for a given round
        """

        path = "/v2/deltas/{round}"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LedgerStateDelta)

        raise UnexpectedStatusError(response.status_code, response.text)

    def ledger_state_delta_for_transaction_group(
        self,
        id_: str,
    ) -> models.LedgerStateDelta:
        """
        Get a LedgerStateDelta object for a given transaction group
        """

        path = "/v2/deltas/txn/group/{id}"
        path = path.replace("{id}", str(id_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LedgerStateDelta)

        raise UnexpectedStatusError(response.status_code, response.text)

    def light_block_header_proof(
        self,
        round_: int,
    ) -> models.LightBlockHeaderProof:
        """
        Gets a proof for a given light block header inside a state proof commitment
        """

        path = "/v2/blocks/{round}/lightheader/proof"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LightBlockHeaderProof)

        raise UnexpectedStatusError(response.status_code, response.text)

    def pending_transaction_information(
        self,
        txid: str,
    ) -> models.PendingTransactionResponse:
        """
        Get a specific pending transaction.
        """

        path = "/v2/transactions/pending/{txid}"
        path = path.replace("{txid}", str(txid))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PendingTransactionResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def pending_transactions(
        self,
        *,
        max_: int | None = None,
    ) -> models.PendingTransactionsResponse:
        """
        Get a list of unconfirmed transactions currently in the transaction pool.
        """

        path = "/v2/transactions/pending"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if max_ is not None:
            params["max"] = max_

        accept_value: str | None = None

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PendingTransactionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def pending_transactions_by_address(
        self,
        address: str,
        *,
        max_: int | None = None,
    ) -> models.PendingTransactionsResponse:
        """
        Get a list of unconfirmed transactions currently in the transaction pool by address.
        """

        path = "/v2/accounts/{address}/transactions/pending"
        path = path.replace("{address}", str(address))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if max_ is not None:
            params["max"] = max_

        accept_value: str | None = None

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PendingTransactionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def ready(
        self,
    ) -> None:
        """
        Returns OK if healthy and fully caught up.
        """

        path = "/ready"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def set_block_time_stamp_offset(
        self,
        offset: int,
    ) -> None:
        """
        Given a timestamp offset in seconds, adds the offset to every subsequent block header's
        timestamp.
        """

        path = "/v2/devmode/blocks/offset/{offset}"
        path = path.replace("{offset}", str(offset))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def set_sync_round(
        self,
        round_: int,
    ) -> None:
        """
        Given a round, tells the ledger to keep that round in its cache.
        """

        path = "/v2/ledger/sync/{round}"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def simulate_transactions(
        self,
        body: models.SimulateRequest,
    ) -> models.SimulateResponse:
        """
        Simulates a raw transaction or transaction group as it would be evaluated on the
        network. The simulation will use blockchain state from the latest committed round.
        """

        path = "/v2/transactions/simulate"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/msgpack"]

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        if "application/msgpack" in body_media_types:
            body_media_types = ["application/msgpack"]

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "model": "SimulateRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SimulateResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def state_proof(
        self,
        round_: int,
    ) -> models.StateProof:
        """
        Get a state proof that covers a given round
        """

        path = "/v2/stateproofs/{round}"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.StateProof)

        raise UnexpectedStatusError(response.status_code, response.text)

    def status(
        self,
    ) -> models.NodeStatusResponse:
        """
        Gets the current node status.
        """

        path = "/v2/status"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.NodeStatusResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def status_after_block(
        self,
        round_: int,
    ) -> models.NodeStatusResponse:
        """
        Gets the node status after waiting for a round after the given round.
        """

        path = "/v2/status/wait-for-block-after/{round}"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.NodeStatusResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def supply(
        self,
    ) -> models.SupplyResponse:
        """
        Get the current supply reported by the ledger.
        """

        path = "/v2/ledger/supply"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SupplyResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sync_round(
        self,
    ) -> models.GetSyncRoundResponse:
        """
        Returns the minimum sync round the ledger is keeping in cache.
        """

        path = "/v2/ledger/sync"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetSyncRoundResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def teal_compile(
        self,
        body: bytes,
        *,
        sourcemap: bool | None = None,
    ) -> models.CompileResponse:
        """
        Compile TEAL source code to binary, produce its hash
        """

        path = "/v2/teal/compile"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if sourcemap is not None:
            params["sourcemap"] = sourcemap

        accept_value: str | None = None

        body_media_types = ["text/plain"]

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "is_binary": True,
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.CompileResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def teal_disassemble(
        self,
        body: bytes,
    ) -> models.DisassembleResponse:
        """
        Disassemble program bytes into the TEAL source code.
        """

        path = "/v2/teal/disassemble"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/x-binary"]

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "is_binary": True,
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.DisassembleResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def transaction_group_ledger_state_deltas_for_round(
        self,
        round_: int,
    ) -> models.TransactionGroupLedgerStateDeltasForRound:
        """
        Get LedgerStateDelta objects for all transaction groups in a given round
        """

        path = "/v2/deltas/{round}/txn/group"
        path = path.replace("{round}", str(round_))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        params["format"] = "msgpack"
        accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/msgpack")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TransactionGroupLedgerStateDeltasForRound)

        raise UnexpectedStatusError(response.status_code, response.text)

    def transaction_proof(
        self,
        round_: int,
        txid: str,
        *,
        response_format: Literal["json", "msgpack"] | None = None,
        hashtype: str | None = None,
    ) -> models.TransactionProof:
        """
        Get a proof for a transaction in a block.
        """

        path = "/v2/blocks/{round}/transactions/{txid}/proof"
        path = path.replace("{round}", str(round_))

        path = path.replace("{txid}", str(txid))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if hashtype is not None:
            params["hashtype"] = hashtype

        accept_value: str | None = None

        selected_format = response_format

        if selected_format == "msgpack":
            params["format"] = "msgpack"
            accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TransactionProof)

        raise UnexpectedStatusError(response.status_code, response.text)

    def unset_sync_round(
        self,
    ) -> None:
        """
        Removes minimum sync round restriction from the ledger.
        """

        path = "/v2/ledger/sync"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "DELETE",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def version(
        self,
    ) -> models.VersionContainsTheCurrentAlgodVersion:
        """
        Retrieves the supported API versions, binary build versions, and genesis information.
        """

        path = "/versions"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.VersionContainsTheCurrentAlgodVersion)

        raise UnexpectedStatusError(response.status_code, response.text)

    def send_raw_transaction(
        self,
        stx_or_stxs: bytes | bytearray | memoryview | Sequence[bytes | bytearray | memoryview],
    ) -> models.PostTransactionsResponse:
        """
        Send a signed transaction or array of signed transactions to the network.
        """

        payload: bytes
        if isinstance(stx_or_stxs, bytes | bytearray | memoryview):
            payload = bytes(stx_or_stxs)
        elif isinstance(stx_or_stxs, Sequence):
            segments: list[bytes] = []
            for value in stx_or_stxs:
                if not isinstance(value, bytes | bytearray | memoryview):
                    raise TypeError("All sequence elements must be bytes-like")
                segments.append(bytes(value))
            payload = b"".join(segments)
        else:
            raise TypeError("stx_or_stxs must be bytes or a sequence of bytes-like values")

        return self._raw_transaction(payload)

    def application_box_by_name(
        self,
        application_id: int,
        box_name: bytes | bytearray | memoryview | str,
    ) -> models.Box:
        """
        Given an application ID and box name, return the corresponding box details.
        """

        box_bytes = box_name.encode() if isinstance(box_name, str) else bytes(box_name)
        encoded_name = "b64:" + b64encode(box_bytes).decode("ascii")
        return self._application_box_by_name(application_id, name=encoded_name)

    def suggested_params(self) -> models.SuggestedParams:
        """
        Return the common parameters required for assembling a transaction.
        """

        txn_params = self._transaction_params()
        last_round = txn_params.last_round
        return models.SuggestedParams(
            consensus_version=txn_params.consensus_version,
            fee=txn_params.fee,
            genesis_hash=txn_params.genesis_hash,
            genesis_id=txn_params.genesis_id,
            min_fee=txn_params.min_fee,
            flat_fee=False,
            first_valid=last_round,
            last_valid=last_round + 1000,
        )

    def _assign_body(
        self,
        request_kwargs: dict[str, Any],
        payload: object,
        descriptor: dict[str, object],
        media_types: list[str],
    ) -> None:
        encoded = self._encode_payload(payload, descriptor)
        binary_types = {"application/x-binary", "application/octet-stream"}
        if bool(descriptor.get("is_binary")) or any(mt in binary_types for mt in media_types):
            if encoded is None:
                return
            request_kwargs["content"] = encoded
            if media_types:
                request_kwargs.setdefault("headers", {})["content-type"] = media_types[0]
            else:
                request_kwargs.setdefault("headers", {})["content-type"] = "application/octet-stream"
        elif "application/json" in media_types:
            request_kwargs["json"] = encoded
        elif "application/msgpack" in media_types:
            request_kwargs["content"] = msgpack.packb(encoded, use_bin_type=True)
            request_kwargs.setdefault("headers", {})["content-type"] = "application/msgpack"
        else:
            request_kwargs["json"] = encoded

    def _encode_payload(self, payload: object, descriptor: dict[str, object]) -> object:
        if payload is None:
            return None
        if is_dataclass(payload):
            return to_wire(payload)
        list_model = descriptor.get("list_model")
        if list_model and isinstance(payload, list):
            return [to_wire(item) if is_dataclass(item) else item for item in payload]
        return payload

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        model: type[ModelT],
        is_binary: bool = False,
        raw_msgpack: bool = False,
    ) -> ModelT: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        list_model: type[ListModelT],
        is_binary: bool = False,
        raw_msgpack: bool = False,
    ) -> list[ListModelT]: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        type_: type[PrimitiveT],
        is_binary: bool = False,
        raw_msgpack: bool = False,
    ) -> PrimitiveT: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        is_binary: Literal[True],
        raw_msgpack: bool = False,
    ) -> bytes: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        raw_msgpack: Literal[True],
    ) -> bytes: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        type_: None = None,
        is_binary: bool = False,
        raw_msgpack: bool = False,
    ) -> object: ...

    def _decode_response(
        self,
        response: httpx.Response,
        *,
        model: type[Any] | None = None,
        list_model: type[Any] | None = None,
        type_: type[Any] | None = None,
        is_binary: bool = False,
        raw_msgpack: bool = False,
    ) -> object:
        if is_binary or raw_msgpack:
            return response.content
        content_type = response.headers.get("content-type", "application/json")
        if "msgpack" in content_type:
            # Handle msgpack unpacking with support for unhashable keys
            # Use Unpacker for more control over the unpacking process
            unpacker = msgpack.Unpacker(
                raw=True,
                strict_map_key=False,
                object_pairs_hook=self._msgpack_pairs_hook,
            )
            unpacker.feed(response.content)
            try:
                data = unpacker.unpack()
            except TypeError:
                # If unpacking fails due to unhashable keys, try without the hook
                # and handle in normalization
                unpacker = msgpack.Unpacker(raw=True, strict_map_key=False)
                unpacker.feed(response.content)
                data = unpacker.unpack()
            data = self._normalize_msgpack(data)
        elif content_type.startswith("application/json"):
            data = response.json()
        else:
            data = response.text
        if model is not None:
            return from_wire(model, data)
        if list_model is not None:
            return [from_wire(list_model, item) for item in data]
        if type_ is not None:
            return data
        return data

    def _normalize_msgpack(self, value: object) -> object:
        # Handle pairs returned from msgpack_pairs_hook when keys are unhashable
        _pair_length = 2
        if isinstance(value, list) and value and isinstance(value[0], tuple | list) and len(value[0]) == _pair_length:
            # Convert to dict with normalized keys
            pairs_dict: dict[object, object] = {}
            for pair in value:
                if isinstance(pair, tuple | list) and len(pair) == _pair_length:
                    k, v = pair
                    # For unhashable keys (like dict keys), use a tuple representation
                    try:
                        normalized_key = self._coerce_msgpack_key(k)
                        pairs_dict[normalized_key] = self._normalize_msgpack(v)
                    except TypeError:
                        # Key is unhashable - use tuple representation
                        normalized_key = ("__unhashable__", id(k), str(k))
                        pairs_dict[normalized_key] = self._normalize_msgpack(v)
            return pairs_dict
        if isinstance(value, dict):
            # Safely normalize maps: coerce string/bytes keys, but tolerate complex/unhashable keys
            try:
                normalized_dict: dict[object, object] = {}
                for key, item in value.items():
                    normalized_dict[self._coerce_msgpack_key(key)] = self._normalize_msgpack(item)
                return normalized_dict
            except TypeError:
                # Some maps can decode to object/dict keys; keep original keys and
                # only normalize values to avoid "unhashable type: 'dict'" errors.
                for k, item in list(value.items()):
                    value[k] = self._normalize_msgpack(item)
                return value
        if isinstance(value, list):
            return [self._normalize_msgpack(item) for item in value]
        return value

    def _coerce_msgpack_key(self, key: object) -> object:
        if isinstance(key, bytes):
            try:
                return key.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                return key
        return key

    def _msgpack_pairs_hook(self, pairs: list[tuple[object, object]] | list[list[object]]) -> dict[object, object]:
        # Convert pairs to dict, handling unhashable keys by converting them to hashable tuples
        out: dict[object, object] = {}
        _hashable_type_tuple = (str, int, float, bool, type(None), bytes)

        for k, v in pairs:
            if isinstance(k, dict | list | set):
                # Convert unhashable key to hashable tuple
                hashable_key: tuple[str, object]
                if isinstance(k, dict):
                    try:
                        hashable_key = (_UNHASHABLE_PREFIXES["dict"], tuple(sorted(k.items())))
                    except TypeError:
                        hashable_key = (_UNHASHABLE_PREFIXES["dict"], str(k))
                elif isinstance(k, list):
                    prefix = _UNHASHABLE_PREFIXES["list"]
                    hashable_key = (prefix, tuple(k) if all(isinstance(x, _hashable_type_tuple) for x in k) else str(k))
                else:  # set
                    prefix = _UNHASHABLE_PREFIXES["set"]
                    if all(isinstance(x, _hashable_type_tuple) for x in k):
                        hashable_key = (prefix, tuple(sorted(k)))
                    else:
                        hashable_key = (prefix, str(k))
                out[hashable_key] = v
            else:
                # Key should be hashable, use as-is
                try:
                    out[k] = v
                except TypeError:
                    # Unexpected unhashable type, convert to tuple
                    out[(_UNHASHABLE_PREFIXES["generic"], str(type(k).__name__), str(k))] = v
        return out
