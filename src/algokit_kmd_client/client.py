# AUTO-GENERATED: oas_generator


from dataclasses import is_dataclass
from typing import Any, Literal, TypeVar, overload

import httpx
import msgpack

from algokit_common.serde import from_wire, to_wire

from . import models
from .config import ClientConfig
from .exceptions import UnexpectedStatusError
from .types import Headers

ModelT = TypeVar("ModelT")
ListModelT = TypeVar("ListModelT")
PrimitiveT = TypeVar("PrimitiveT")


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
    ) -> models.PostwalletResponse:
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
                    "is_binary": False,
                    "model": "CreateWalletRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostwalletResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def delete_key(
        self,
        body: models.DeleteKeyRequest,
    ) -> models.DeletekeyResponse:
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
                    "is_binary": False,
                    "model": "DeleteKeyRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.DeletekeyResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def delete_multisig(
        self,
        body: models.DeleteMultisigRequest,
    ) -> models.DeletemultisigResponse:
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
                    "is_binary": False,
                    "model": "DeleteMultisigRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.DeletemultisigResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_key(
        self,
        body: models.ExportKeyRequest,
    ) -> models.PostkeyExportResponse:
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
                    "is_binary": False,
                    "model": "ExportKeyRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostkeyExportResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_master_key(
        self,
        body: models.ExportMasterKeyRequest,
    ) -> models.PostmasterKeyExportResponse:
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
                    "is_binary": False,
                    "model": "ExportMasterKeyRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostmasterKeyExportResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def export_multisig(
        self,
        body: models.ExportMultisigRequest,
    ) -> models.PostmultisigExportResponse:
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
                    "is_binary": False,
                    "model": "ExportMultisigRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostmultisigExportResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def generate_key(
        self,
        body: models.GenerateKeyRequest,
    ) -> models.PostkeyResponse:
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
                    "is_binary": False,
                    "model": "GenerateKeyRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostkeyResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_version(
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
                    "is_binary": False,
                    "model": "VersionsRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.VersionsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_wallet_info(
        self,
        body: models.WalletInfoRequest,
    ) -> models.PostwalletInfoResponse:
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
                    "is_binary": False,
                    "model": "WalletInfoRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostwalletInfoResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def import_key(
        self,
        body: models.ImportKeyRequest,
    ) -> models.PostkeyImportResponse:
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
                    "is_binary": False,
                    "model": "ImportKeyRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostkeyImportResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def import_multisig(
        self,
        body: models.ImportMultisigRequest,
    ) -> models.PostmultisigImportResponse:
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
                    "is_binary": False,
                    "model": "ImportMultisigRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostmultisigImportResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def init_wallet_handle_token(
        self,
        body: models.InitWalletHandleTokenRequest,
    ) -> models.PostwalletInitResponse:
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
                    "is_binary": False,
                    "model": "InitWalletHandleTokenRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostwalletInitResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_keys_in_wallet(
        self,
        body: models.ListKeysRequest,
    ) -> models.PostkeyListResponse:
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
                    "is_binary": False,
                    "model": "ListKeysRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostkeyListResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_multisg(
        self,
        body: models.ListMultisigRequest,
    ) -> models.PostmultisigListResponse:
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
                    "is_binary": False,
                    "model": "ListMultisigRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostmultisigListResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def list_wallets(
        self,
        *,
        body: models.ListWalletsRequest | None = None,
    ) -> models.GetwalletsResponse:
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
                    "is_binary": False,
                    "model": "ListWalletsRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetwalletsResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def release_wallet_handle_token(
        self,
        body: models.ReleaseWalletHandleTokenRequest,
    ) -> models.PostwalletReleaseResponse:
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
                    "is_binary": False,
                    "model": "ReleaseWalletHandleTokenRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostwalletReleaseResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def rename_wallet(
        self,
        body: models.RenameWalletRequest,
    ) -> models.PostwalletRenameResponse:
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
                    "is_binary": False,
                    "model": "RenameWalletRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostwalletRenameResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def renew_wallet_handle_token(
        self,
        body: models.RenewWalletHandleTokenRequest,
    ) -> models.PostwalletRenewResponse:
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
                    "is_binary": False,
                    "model": "RenewWalletHandleTokenRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostwalletRenewResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_multisig_program(
        self,
        body: models.SignProgramMultisigRequest,
    ) -> models.PostmultisigProgramSignResponse:
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
                    "is_binary": False,
                    "model": "SignProgramMultisigRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostmultisigProgramSignResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_multisig_transaction(
        self,
        body: models.SignMultisigRequest,
    ) -> models.PostmultisigTransactionSignResponse:
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
                    "is_binary": False,
                    "model": "SignMultisigRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostmultisigTransactionSignResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_program(
        self,
        body: models.SignProgramRequest,
    ) -> models.PostprogramSignResponse:
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
                    "is_binary": False,
                    "model": "SignProgramRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PostprogramSignResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def sign_transaction(
        self,
        body: models.SignTransactionRequest,
    ) -> models.PosttransactionSignResponse:
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
                    "is_binary": False,
                    "model": "SignTransactionRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PosttransactionSignResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def swagger_handler(
        self,
    ) -> str:
        """
        Gets the current swagger spec.
        """

        path = "/swagger.json"
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, type_=str)

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
    ) -> ModelT: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        list_model: type[ListModelT],
        is_binary: bool = False,
    ) -> list[ListModelT]: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        type_: type[PrimitiveT],
        is_binary: bool = False,
    ) -> PrimitiveT: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        is_binary: Literal[True],
    ) -> bytes: ...

    @overload
    def _decode_response(
        self,
        response: httpx.Response,
        *,
        type_: None = None,
        is_binary: bool = False,
    ) -> object: ...

    def _decode_response(
        self,
        response: httpx.Response,
        *,
        model: type[Any] | None = None,
        list_model: type[Any] | None = None,
        type_: type[Any] | None = None,
        is_binary: bool = False,
    ) -> object:
        if is_binary:
            return response.content
        content_type = response.headers.get("content-type", "application/json")
        if "msgpack" in content_type:
            data = msgpack.unpackb(response.content, raw=False, strict_map_key=False)
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
        if isinstance(value, dict):
            normalized: dict[object, object] = {}
            for key, item in value.items():
                normalized[self._ensure_str_key(key)] = self._normalize_msgpack(item)
            return normalized
        if isinstance(value, list):
            return [self._normalize_msgpack(item) for item in value]
        return value

    def _ensure_str_key(self, key: object) -> object:
        if isinstance(key, bytes):
            try:
                return key.decode("utf-8")
            except UnicodeDecodeError:
                return key
        return key
