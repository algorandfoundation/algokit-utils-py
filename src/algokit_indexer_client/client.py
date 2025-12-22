# AUTO-GENERATED: oas_generator
import random
import time
from dataclasses import is_dataclass
from datetime import datetime
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


class IndexerClient:
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

    # common

    def health_check(
        self,
    ) -> models.HealthCheck:
        """
        Returns 200 if healthy.
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
            return self._decode_response(response, model=models.HealthCheck)

        raise UnexpectedStatusError(response.status_code, response.text)

    # lookup

    def lookup_account_app_local_states(
        self,
        account_id: str,
        *,
        application_id: int | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.ApplicationLocalStatesResponse:
        """
        Lookup an account's asset holdings, optionally for a specific ID.
        """

        path = "/v2/accounts/{account-id}/apps-local-state"
        path = path.replace("{account-id}", str(account_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if application_id is not None:
            params["application-id"] = application_id

        if include_all is not None:
            params["include-all"] = include_all

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

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
            return self._decode_response(response, model=models.ApplicationLocalStatesResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_assets(
        self,
        account_id: str,
        *,
        asset_id: int | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.AssetHoldingsResponse:
        """
        Lookup an account's asset holdings, optionally for a specific ID.
        """

        path = "/v2/accounts/{account-id}/assets"
        path = path.replace("{account-id}", str(account_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if asset_id is not None:
            params["asset-id"] = asset_id

        if include_all is not None:
            params["include-all"] = include_all

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

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
            return self._decode_response(response, model=models.AssetHoldingsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_by_id(
        self,
        account_id: str,
        *,
        round_: int | None = None,
        include_all: bool | None = None,
        exclude: list[str] | None = None,
    ) -> models.AccountResponse:
        """
        Lookup account information.
        """

        path = "/v2/accounts/{account-id}"
        path = path.replace("{account-id}", str(account_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if round_ is not None:
            params["round"] = round_

        if include_all is not None:
            params["include-all"] = include_all

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
            return self._decode_response(response, model=models.AccountResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_created_applications(
        self,
        account_id: str,
        *,
        application_id: int | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.ApplicationsResponse:
        """
        Lookup an account's created application parameters, optionally for a specific ID.
        """

        path = "/v2/accounts/{account-id}/created-applications"
        path = path.replace("{account-id}", str(account_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if application_id is not None:
            params["application-id"] = application_id

        if include_all is not None:
            params["include-all"] = include_all

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

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
            return self._decode_response(response, model=models.ApplicationsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_created_assets(
        self,
        account_id: str,
        *,
        asset_id: int | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.AssetsResponse:
        """
        Lookup an account's created asset parameters, optionally for a specific ID.
        """

        path = "/v2/accounts/{account-id}/created-assets"
        path = path.replace("{account-id}", str(account_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if asset_id is not None:
            params["asset-id"] = asset_id

        if include_all is not None:
            params["include-all"] = include_all

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

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
            return self._decode_response(response, model=models.AssetsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_transactions(  # noqa: C901, PLR0912, PLR0913
        self,
        account_id: str,
        *,
        limit: int | None = None,
        next_: str | None = None,
        note_prefix: str | None = None,
        tx_type: str | None = None,
        sig_type: str | None = None,
        txid: str | None = None,
        round_: int | None = None,
        min_round: int | None = None,
        max_round: int | None = None,
        asset_id: int | None = None,
        before_time: datetime | None = None,
        after_time: datetime | None = None,
        currency_greater_than: int | None = None,
        currency_less_than: int | None = None,
        rekey_to: bool | None = None,
    ) -> models.TransactionsResponse:
        """
        Lookup account transactions. Transactions are returned newest to oldest.
        """

        path = "/v2/accounts/{account-id}/transactions"
        path = path.replace("{account-id}", str(account_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if note_prefix is not None:
            params["note-prefix"] = note_prefix

        if tx_type is not None:
            params["tx-type"] = tx_type

        if sig_type is not None:
            params["sig-type"] = sig_type

        if txid is not None:
            params["txid"] = txid

        if round_ is not None:
            params["round"] = round_

        if min_round is not None:
            params["min-round"] = min_round

        if max_round is not None:
            params["max-round"] = max_round

        if asset_id is not None:
            params["asset-id"] = asset_id

        if before_time is not None:
            params["before-time"] = before_time

        if after_time is not None:
            params["after-time"] = after_time

        if currency_greater_than is not None:
            params["currency-greater-than"] = currency_greater_than

        if currency_less_than is not None:
            params["currency-less-than"] = currency_less_than

        if rekey_to is not None:
            params["rekey-to"] = rekey_to

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
            return self._decode_response(response, model=models.TransactionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_application_box_by_idand_name(
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

    def lookup_application_by_id(
        self,
        application_id: int,
        *,
        include_all: bool | None = None,
    ) -> models.ApplicationResponse:
        """
        Lookup application.
        """

        path = "/v2/applications/{application-id}"
        path = path.replace("{application-id}", str(application_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if include_all is not None:
            params["include-all"] = include_all

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
            return self._decode_response(response, model=models.ApplicationResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_application_logs_by_id(
        self,
        application_id: int,
        *,
        limit: int | None = None,
        next_: str | None = None,
        txid: str | None = None,
        min_round: int | None = None,
        max_round: int | None = None,
        sender_address: str | None = None,
    ) -> models.ApplicationLogsResponse:
        """
        Lookup application logs.
        """

        path = "/v2/applications/{application-id}/logs"
        path = path.replace("{application-id}", str(application_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if txid is not None:
            params["txid"] = txid

        if min_round is not None:
            params["min-round"] = min_round

        if max_round is not None:
            params["max-round"] = max_round

        if sender_address is not None:
            params["sender-address"] = sender_address

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
            return self._decode_response(response, model=models.ApplicationLogsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_asset_balances(
        self,
        asset_id: int,
        *,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
        currency_greater_than: int | None = None,
        currency_less_than: int | None = None,
    ) -> models.AssetBalancesResponse:
        """
        Lookup the list of accounts who hold this asset
        """

        path = "/v2/assets/{asset-id}/balances"
        path = path.replace("{asset-id}", str(asset_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if include_all is not None:
            params["include-all"] = include_all

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if currency_greater_than is not None:
            params["currency-greater-than"] = currency_greater_than

        if currency_less_than is not None:
            params["currency-less-than"] = currency_less_than

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
            return self._decode_response(response, model=models.AssetBalancesResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_asset_by_id(
        self,
        asset_id: int,
        *,
        include_all: bool | None = None,
    ) -> models.AssetResponse:
        """
        Lookup asset information.
        """

        path = "/v2/assets/{asset-id}"
        path = path.replace("{asset-id}", str(asset_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if include_all is not None:
            params["include-all"] = include_all

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
            return self._decode_response(response, model=models.AssetResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_asset_transactions(  # noqa: C901, PLR0912, PLR0913
        self,
        asset_id: int,
        *,
        limit: int | None = None,
        next_: str | None = None,
        note_prefix: str | None = None,
        tx_type: str | None = None,
        sig_type: str | None = None,
        txid: str | None = None,
        round_: int | None = None,
        min_round: int | None = None,
        max_round: int | None = None,
        before_time: datetime | None = None,
        after_time: datetime | None = None,
        currency_greater_than: int | None = None,
        currency_less_than: int | None = None,
        address: str | None = None,
        address_role: str | None = None,
        exclude_close_to: bool | None = None,
        rekey_to: bool | None = None,
    ) -> models.TransactionsResponse:
        """
        Lookup transactions for an asset. Transactions are returned oldest to newest.
        """

        path = "/v2/assets/{asset-id}/transactions"
        path = path.replace("{asset-id}", str(asset_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if note_prefix is not None:
            params["note-prefix"] = note_prefix

        if tx_type is not None:
            params["tx-type"] = tx_type

        if sig_type is not None:
            params["sig-type"] = sig_type

        if txid is not None:
            params["txid"] = txid

        if round_ is not None:
            params["round"] = round_

        if min_round is not None:
            params["min-round"] = min_round

        if max_round is not None:
            params["max-round"] = max_round

        if before_time is not None:
            params["before-time"] = before_time

        if after_time is not None:
            params["after-time"] = after_time

        if currency_greater_than is not None:
            params["currency-greater-than"] = currency_greater_than

        if currency_less_than is not None:
            params["currency-less-than"] = currency_less_than

        if address is not None:
            params["address"] = address

        if address_role is not None:
            params["address-role"] = address_role

        if exclude_close_to is not None:
            params["exclude-close-to"] = exclude_close_to

        if rekey_to is not None:
            params["rekey-to"] = rekey_to

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
            return self._decode_response(response, model=models.TransactionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_block(
        self,
        round_number: int,
        *,
        header_only: bool | None = None,
    ) -> models.Block:
        """
        Lookup block.
        """

        path = "/v2/blocks/{round-number}"
        path = path.replace("{round-number}", str(round_number))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if header_only is not None:
            params["header-only"] = header_only

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
            return self._decode_response(response, model=models.Block)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_transaction_by_id(
        self,
        txid: str,
    ) -> models.TransactionResponse:
        """
        Lookup a single transaction.
        """

        path = "/v2/transactions/{txid}"
        path = path.replace("{txid}", str(txid))

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
            return self._decode_response(response, model=models.TransactionResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    # search

    def search_for_accounts(  # noqa: C901, PLR0913
        self,
        *,
        asset_id: int | None = None,
        limit: int | None = None,
        next_: str | None = None,
        currency_greater_than: int | None = None,
        include_all: bool | None = None,
        exclude: list[str] | None = None,
        currency_less_than: int | None = None,
        auth_addr: str | None = None,
        round_: int | None = None,
        application_id: int | None = None,
        online_only: bool | None = None,
    ) -> models.AccountsResponse:
        """
        Search for accounts.
        """

        path = "/v2/accounts"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if asset_id is not None:
            params["asset-id"] = asset_id

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if currency_greater_than is not None:
            params["currency-greater-than"] = currency_greater_than

        if include_all is not None:
            params["include-all"] = include_all

        if exclude is not None:
            params["exclude"] = exclude

        if currency_less_than is not None:
            params["currency-less-than"] = currency_less_than

        if auth_addr is not None:
            params["auth-addr"] = auth_addr

        if round_ is not None:
            params["round"] = round_

        if application_id is not None:
            params["application-id"] = application_id

        if online_only is not None:
            params["online-only"] = online_only

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
            return self._decode_response(response, model=models.AccountsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def search_for_application_boxes(
        self,
        application_id: int,
        *,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.BoxesResponse:
        """
        Get box names for a given application.
        """

        path = "/v2/applications/{application-id}/boxes"
        path = path.replace("{application-id}", str(application_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

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

    def search_for_applications(
        self,
        *,
        application_id: int | None = None,
        creator: str | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.ApplicationsResponse:
        """
        Search for applications
        """

        path = "/v2/applications"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if application_id is not None:
            params["application-id"] = application_id

        if creator is not None:
            params["creator"] = creator

        if include_all is not None:
            params["include-all"] = include_all

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

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
            return self._decode_response(response, model=models.ApplicationsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def search_for_assets(
        self,
        *,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
        creator: str | None = None,
        name: str | None = None,
        unit: str | None = None,
        asset_id: int | None = None,
    ) -> models.AssetsResponse:
        """
        Search for assets.
        """

        path = "/v2/assets"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if include_all is not None:
            params["include-all"] = include_all

        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if creator is not None:
            params["creator"] = creator

        if name is not None:
            params["name"] = name

        if unit is not None:
            params["unit"] = unit

        if asset_id is not None:
            params["asset-id"] = asset_id

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
            return self._decode_response(response, model=models.AssetsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def search_for_block_headers(  # noqa: C901
        self,
        *,
        limit: int | None = None,
        next_: str | None = None,
        min_round: int | None = None,
        max_round: int | None = None,
        before_time: datetime | None = None,
        after_time: datetime | None = None,
        proposers: list[str] | None = None,
        expired: list[str] | None = None,
        absent: list[str] | None = None,
    ) -> models.BlockHeadersResponse:
        """
        Search for block headers. Block headers are returned in ascending round order.
        Transactions are not included in the output.
        """

        path = "/v2/block-headers"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if min_round is not None:
            params["min-round"] = min_round

        if max_round is not None:
            params["max-round"] = max_round

        if before_time is not None:
            params["before-time"] = before_time

        if after_time is not None:
            params["after-time"] = after_time

        if proposers is not None:
            params["proposers"] = proposers

        if expired is not None:
            params["expired"] = expired

        if absent is not None:
            params["absent"] = absent

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
            return self._decode_response(response, model=models.BlockHeadersResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def search_for_transactions(  # noqa: C901, PLR0912, PLR0913
        self,
        *,
        limit: int | None = None,
        next_: str | None = None,
        note_prefix: str | None = None,
        tx_type: str | None = None,
        sig_type: str | None = None,
        group_id: str | None = None,
        txid: str | None = None,
        round_: int | None = None,
        min_round: int | None = None,
        max_round: int | None = None,
        asset_id: int | None = None,
        before_time: datetime | None = None,
        after_time: datetime | None = None,
        currency_greater_than: int | None = None,
        currency_less_than: int | None = None,
        address: str | None = None,
        address_role: str | None = None,
        exclude_close_to: bool | None = None,
        rekey_to: bool | None = None,
        application_id: int | None = None,
    ) -> models.TransactionsResponse:
        """
        Search for transactions. Transactions are returned oldest to newest unless the address
        parameter is used, in which case results are returned newest to oldest.
        """

        path = "/v2/transactions"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if limit is not None:
            params["limit"] = limit

        if next_ is not None:
            params["next"] = next_

        if note_prefix is not None:
            params["note-prefix"] = note_prefix

        if tx_type is not None:
            params["tx-type"] = tx_type

        if sig_type is not None:
            params["sig-type"] = sig_type

        if group_id is not None:
            params["group-id"] = group_id

        if txid is not None:
            params["txid"] = txid

        if round_ is not None:
            params["round"] = round_

        if min_round is not None:
            params["min-round"] = min_round

        if max_round is not None:
            params["max-round"] = max_round

        if asset_id is not None:
            params["asset-id"] = asset_id

        if before_time is not None:
            params["before-time"] = before_time

        if after_time is not None:
            params["after-time"] = after_time

        if currency_greater_than is not None:
            params["currency-greater-than"] = currency_greater_than

        if currency_less_than is not None:
            params["currency-less-than"] = currency_less_than

        if address is not None:
            params["address"] = address

        if address_role is not None:
            params["address-role"] = address_role

        if exclude_close_to is not None:
            params["exclude-close-to"] = exclude_close_to

        if rekey_to is not None:
            params["rekey-to"] = rekey_to

        if application_id is not None:
            params["application-id"] = application_id

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
            return self._decode_response(response, model=models.TransactionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

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
