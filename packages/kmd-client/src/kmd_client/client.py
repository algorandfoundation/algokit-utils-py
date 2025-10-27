from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any

import httpx
import msgpack
from algokit_common.serde import from_wire, to_wire

from . import models
from .config import ClientConfig
from .exceptions import UnexpectedStatusError
from .types import Headers


class KmdClient:
    def __init__(self, config: ClientConfig | None = None, *, http_client: httpx.Client | None = None) -> None:
        self._config = config or ClientConfig()
        self._client = http_client or httpx.Client(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            verify=self._config.verify,
        )

    def close(self) -> None:
        self._client.close()

    # default

    def create_wallet(
        self,
        body: models.CreateWalletRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostwalletResponse:
        """
        Create a wallet
        """

        path = "/v1/wallet"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "CreateWalletRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostwalletResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def delete_key(
        self,
        body: models.DeleteKeyRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.DeletekeyResponse:
        """
        Delete a key
        """

        path = "/v1/key"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "DeleteKeyRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "DeletekeyResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def delete_multisig(
        self,
        body: models.DeleteMultisigRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.DeletemultisigResponse:
        """
        Delete a multisig
        """

        path = "/v1/multisig"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "DeleteMultisigRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "DeletemultisigResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_key(
        self,
        body: models.ExportKeyRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostkeyExportResponse:
        """
        Export a key
        """

        path = "/v1/key/export"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ExportKeyRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostkeyExportResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_master_key(
        self,
        body: models.ExportMasterKeyRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostmasterKeyExportResponse:
        """
        Export the master derivation key from a wallet
        """

        path = "/v1/master-key/export"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ExportMasterKeyRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostmasterKeyExportResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_multisig(
        self,
        body: models.ExportMultisigRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostmultisigExportResponse:
        """
        Export multisig address metadata
        """

        path = "/v1/multisig/export"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ExportMultisigRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostmultisigExportResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def generate_key(
        self,
        body: models.GenerateKeyRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostkeyResponse:
        """
        Generate a key
        """

        path = "/v1/key"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "GenerateKeyRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostkeyResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_version(
        self,
        *,
        body: models.VersionsRequest | None = None,
        request_timeout: float | None = None,
    ) -> models.VersionsResponse:
        """
        Retrieves the current version
        """

        path = "/versions"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "VersionsRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "VersionsResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_wallet_info(
        self,
        body: models.WalletInfoRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostwalletInfoResponse:
        """
        Get wallet info
        """

        path = "/v1/wallet/info"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "WalletInfoRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostwalletInfoResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def import_key(
        self,
        body: models.ImportKeyRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostkeyImportResponse:
        """
        Import a key
        """

        path = "/v1/key/import"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ImportKeyRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostkeyImportResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def import_multisig(
        self,
        body: models.ImportMultisigRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostmultisigImportResponse:
        """
        Import a multisig account
        """

        path = "/v1/multisig/import"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ImportMultisigRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostmultisigImportResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def init_wallet_handle_token(
        self,
        body: models.InitWalletHandleTokenRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostwalletInitResponse:
        """
        Initialize a wallet handle token
        """

        path = "/v1/wallet/init"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "InitWalletHandleTokenRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostwalletInitResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_keys_in_wallet(
        self,
        body: models.ListKeysRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostkeyListResponse:
        """
        List keys in wallet
        """

        path = "/v1/key/list"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ListKeysRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostkeyListResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_multisg(
        self,
        body: models.ListMultisigRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostmultisigListResponse:
        """
        List multisig accounts
        """

        path = "/v1/multisig/list"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ListMultisigRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostmultisigListResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_wallets(
        self,
        *,
        body: models.ListWalletsRequest | None = None,
        request_timeout: float | None = None,
    ) -> models.GetwalletsResponse:
        """
        List wallets
        """

        path = "/v1/wallets"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ListWalletsRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "GetwalletsResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def release_wallet_handle_token(
        self,
        body: models.ReleaseWalletHandleTokenRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostwalletReleaseResponse:
        """
        Release a wallet handle token
        """

        path = "/v1/wallet/release"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "ReleaseWalletHandleTokenRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostwalletReleaseResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def rename_wallet(
        self,
        body: models.RenameWalletRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostwalletRenameResponse:
        """
        Rename a wallet
        """

        path = "/v1/wallet/rename"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "RenameWalletRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostwalletRenameResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def renew_wallet_handle_token(
        self,
        body: models.RenewWalletHandleTokenRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostwalletRenewResponse:
        """
        Renew a wallet handle token
        """

        path = "/v1/wallet/renew"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "RenewWalletHandleTokenRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostwalletRenewResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_multisig_program(
        self,
        body: models.SignProgramMultisigRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostmultisigProgramSignResponse:
        """
        Sign a program for a multisig account
        """

        path = "/v1/multisig/signprogram"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "SignProgramMultisigRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostmultisigProgramSignResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_multisig_transaction(
        self,
        body: models.SignMultisigRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostmultisigTransactionSignResponse:
        """
        Sign a multisig transaction
        """

        path = "/v1/multisig/sign"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "SignMultisigRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostmultisigTransactionSignResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_program(
        self,
        body: models.SignProgramRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PostprogramSignResponse:
        """
        Sign program
        """

        path = "/v1/program/sign"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "SignProgramRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PostprogramSignResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_transaction(
        self,
        body: models.SignTransactionRequest,
        *,
        request_timeout: float | None = None,
    ) -> models.PosttransactionSignResponse:
        """
        Sign a transaction
        """

        path = "/v1/transaction/sign"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

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
                {"is_binary": False, "model": "SignTransactionRequest"},
                ["application/json"],
                prefer_msgpack=False,
            )

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False, "model": "PosttransactionSignResponse"})

        raise UnexpectedStatusError(response.status_code, response.text)

    def swagger_handler(
        self,
        *,
        request_timeout: float | None = None,
    ) -> str:
        """
        Gets the current swagger spec.
        """

        path = "/swagger.json"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        headers.setdefault("accept", "application/json")

        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(timeout=request_timeout, **request_kwargs)
        if response.is_success:
            return self._decode_response(response, {"is_binary": False})

        raise UnexpectedStatusError(response.status_code, response.text)

    def _assign_body(
        self,
        request_kwargs: dict[str, object],
        payload: object,
        descriptor: dict[str, object],
        media_types: list[str],
        *,
        prefer_msgpack: bool,
    ) -> None:
        encoded = self._encode_payload(payload, descriptor)
        if "application/msgpack" in media_types and prefer_msgpack:
            request_kwargs["content"] = msgpack.packb(encoded, use_bin_type=True)
            request_kwargs["headers"]["content-type"] = "application/msgpack"
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

    def _decode_response(self, response: httpx.Response, descriptor: dict[str, object]) -> object:
        if descriptor.get("is_binary"):
            return response.content
        content_type = response.headers.get("content-type", "application/json")
        if "msgpack" in content_type:
            data = msgpack.unpackb(response.content, raw=False)
        elif content_type.startswith("application/json"):
            data = response.json()
        else:
            data = response.text
        model_name = descriptor.get("model")
        list_model = descriptor.get("list_model")
        if model_name:
            model_cls = getattr(models, model_name)
            return from_wire(model_cls, data)
        if list_model:
            model_cls = getattr(models, list_model)
            return [from_wire(model_cls, item) for item in data]
        return data
