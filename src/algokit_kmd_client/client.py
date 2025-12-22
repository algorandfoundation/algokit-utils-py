# AUTO-GENERATED: oas_generator
import random
import time
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


class KmdClient:
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

    # default

    def create_wallet(
        self,
        body: models.CreateWalletRequest,
    ) -> models.CreateWalletResponse:
        """
        Create a wallet
        """

        path = "/v1/wallet"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "CreateWalletRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.CreateWalletResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def delete_key(
        self,
        body: models.DeleteKeyRequest,
    ) -> None:
        """
        Delete a key
        """

        path = "/v1/key"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "DELETE",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "model": "DeleteKeyRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def delete_multisig(
        self,
        body: models.DeleteMultisigRequest,
    ) -> None:
        """
        Delete a multisig
        """

        path = "/v1/multisig"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "DELETE",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "model": "DeleteMultisigRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_key(
        self,
        body: models.ExportKeyRequest,
    ) -> models.ExportKeyResponse:
        """
        Export a key
        """

        path = "/v1/key/export"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ExportKeyRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ExportKeyResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_master_key(
        self,
        body: models.ExportMasterKeyRequest,
    ) -> models.ExportMasterKeyResponse:
        """
        Export the master derivation key from a wallet
        """

        path = "/v1/master-key/export"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ExportMasterKeyRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ExportMasterKeyResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_multisig(
        self,
        body: models.ExportMultisigRequest,
    ) -> models.ExportMultisigResponse:
        """
        Export multisig address metadata
        """

        path = "/v1/multisig/export"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ExportMultisigRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ExportMultisigResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def generate_key(
        self,
        body: models.GenerateKeyRequest,
    ) -> models.GenerateKeyResponse:
        """
        Generate a key
        """

        path = "/v1/key"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "GenerateKeyRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GenerateKeyResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def import_key(
        self,
        body: models.ImportKeyRequest,
    ) -> models.ImportKeyResponse:
        """
        Import a key
        """

        path = "/v1/key/import"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ImportKeyRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ImportKeyResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def import_multisig(
        self,
        body: models.ImportMultisigRequest,
    ) -> models.ImportMultisigResponse:
        """
        Import a multisig account
        """

        path = "/v1/multisig/import"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ImportMultisigRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ImportMultisigResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def init_wallet_handle(
        self,
        body: models.InitWalletHandleTokenRequest,
    ) -> models.InitWalletHandleTokenResponse:
        """
        Initialize a wallet handle token
        """

        path = "/v1/wallet/init"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "InitWalletHandleTokenRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.InitWalletHandleTokenResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_keys_in_wallet(
        self,
        body: models.ListKeysRequest,
    ) -> models.ListKeysResponse:
        """
        List keys in wallet
        """

        path = "/v1/key/list"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ListKeysRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ListKeysResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_multisig(
        self,
        body: models.ListMultisigRequest,
    ) -> models.ListMultisigResponse:
        """
        List multisig accounts
        """

        path = "/v1/multisig/list"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ListMultisigRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ListMultisigResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_wallets(
        self,
        *,
        body: models.ListWalletsRequest | None = None,
    ) -> models.ListWalletsResponse:
        """
        List wallets
        """

        path = "/v1/wallets"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "model": "ListWalletsRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ListWalletsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def release_wallet_handle_token(
        self,
        body: models.ReleaseWalletHandleTokenRequest,
    ) -> None:
        """
        Release a wallet handle token
        """

        path = "/v1/wallet/release"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "ReleaseWalletHandleTokenRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def rename_wallet(
        self,
        body: models.RenameWalletRequest,
    ) -> models.RenameWalletResponse:
        """
        Rename a wallet
        """

        path = "/v1/wallet/rename"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "RenameWalletRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.RenameWalletResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def renew_wallet_handle_token(
        self,
        body: models.RenewWalletHandleTokenRequest,
    ) -> models.RenewWalletHandleTokenResponse:
        """
        Renew a wallet handle token
        """

        path = "/v1/wallet/renew"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "RenewWalletHandleTokenRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.RenewWalletHandleTokenResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_multisig_program(
        self,
        body: models.SignProgramMultisigRequest,
    ) -> models.SignProgramMultisigResponse:
        """
        Sign a program for a multisig account
        """

        path = "/v1/multisig/signprogram"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "SignProgramMultisigRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SignProgramMultisigResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_multisig_transaction(
        self,
        body: models.SignMultisigTxnRequest,
    ) -> models.SignMultisigResponse:
        """
        Sign a multisig transaction
        """

        path = "/v1/multisig/sign"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "SignMultisigTxnRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SignMultisigResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_program(
        self,
        body: models.SignProgramRequest,
    ) -> models.SignProgramResponse:
        """
        Sign program
        """

        path = "/v1/program/sign"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "SignProgramRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SignProgramResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_transaction(
        self,
        body: models.SignTxnRequest,
    ) -> models.SignTransactionResponse:
        """
        Sign a transaction
        """

        path = "/v1/transaction/sign"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "SignTxnRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SignTransactionResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def version(
        self,
        *,
        body: models.VersionsRequest | None = None,
    ) -> models.VersionsResponse:
        """
        Retrieves the current version
        """

        path = "/versions"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        if body is not None:
            self._assign_body(
                request_kwargs,
                body,
                {
                    "model": "VersionsRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.VersionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def wallet_info(
        self,
        body: models.WalletInfoRequest,
    ) -> models.WalletInfoResponse:
        """
        Get wallet info
        """

        path = "/v1/wallet/info"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json"]

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
                    "model": "WalletInfoRequest",
                },
                body_media_types,
            )

        response = self._request_with_retry(request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.WalletInfoResponse)

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
