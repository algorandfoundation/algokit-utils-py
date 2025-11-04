# AUTO-GENERATED: oas_generator


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

ModelT = TypeVar("ModelT")
ListModelT = TypeVar("ListModelT")
PrimitiveT = TypeVar("PrimitiveT")


class IndexerClient:
    def __init__(self, config: ClientConfig | None = None, *, http_client: httpx.Client | None = None) -> None:
        self._config = config or ClientConfig()
        self._client = http_client or httpx.Client(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            verify=self._config.verify,
        )

    def close(self) -> None:
        self._client.close()

    # common

    def make_health_check(
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

        response = self._client.request(**request_kwargs)
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
    ) -> models.LookupAccountAppLocalStatesResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAccountAppLocalStatesResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_assets(
        self,
        account_id: str,
        *,
        asset_id: int | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.LookupAccountAssetsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAccountAssetsResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_by_id(
        self,
        account_id: str,
        *,
        round_: int | None = None,
        include_all: bool | None = None,
        exclude: list[str] | None = None,
    ) -> models.LookupAccountByIdresponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAccountByIdresponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_created_applications(
        self,
        account_id: str,
        *,
        application_id: int | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.LookupAccountCreatedApplicationsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAccountCreatedApplicationsResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_account_created_assets(
        self,
        account_id: str,
        *,
        asset_id: int | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.LookupAccountCreatedAssetsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAccountCreatedAssetsResponseModel)

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
    ) -> models.LookupAccountTransactionsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAccountTransactionsResponseModel)

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Box)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_application_by_id(
        self,
        application_id: int,
        *,
        include_all: bool | None = None,
    ) -> models.LookupApplicationByIdresponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupApplicationByIdresponseModel)

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
    ) -> models.LookupApplicationLogsByIdresponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupApplicationLogsByIdresponseModel)

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
    ) -> models.LookupAssetBalancesResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAssetBalancesResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_asset_by_id(
        self,
        asset_id: int,
        *,
        include_all: bool | None = None,
    ) -> models.LookupAssetByIdresponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAssetByIdresponseModel)

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
    ) -> models.LookupAssetTransactionsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupAssetTransactionsResponseModel)

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Block)

        raise UnexpectedStatusError(response.status_code, response.text)

    def lookup_transaction(
        self,
        txid: str,
    ) -> models.LookupTransactionResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LookupTransactionResponseModel)

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
    ) -> models.SearchForAccountsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SearchForAccountsResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def search_for_application_boxes(
        self,
        application_id: int,
        *,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.SearchForApplicationBoxesResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SearchForApplicationBoxesResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def search_for_applications(
        self,
        *,
        application_id: int | None = None,
        creator: str | None = None,
        include_all: bool | None = None,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.SearchForApplicationsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SearchForApplicationsResponseModel)

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
    ) -> models.SearchForAssetsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SearchForAssetsResponseModel)

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
    ) -> models.SearchForBlockHeadersResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SearchForBlockHeadersResponseModel)

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
    ) -> models.SearchForTransactionsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SearchForTransactionsResponseModel)

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
