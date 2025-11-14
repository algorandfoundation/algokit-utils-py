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
        self._client = http_client or httpx.Client(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            verify=self._config.verify,
        )

    def close(self) -> None:
        self._client.close()

    # private

    def abort_catchup(
        self,
        catchpoint: str,
    ) -> models.AbortCatchupResponseModel:
        """
        Aborts a catchpoint catchup.
        """

        path = "/v2/catchup/{catchpoint}"
        path = path.replace("{catchpoint}", str(catchpoint))

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.AbortCatchupResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def add_participation_key(
        self,
        body: bytes,
    ) -> models.AddParticipationKeyResponseModel:
        """
        Add a participation key to the node
        """

        path = "/v2/participation"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/msgpack"]

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.AddParticipationKeyResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def append_keys(
        self,
        participation_id: str,
        body: bytes,
    ) -> models.ParticipationKey:
        """
        Append state proof keys to a participation key
        """

        path = "/v2/participation/{participation-id}"
        path = path.replace("{participation-id}", str(participation_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/msgpack"]

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.ParticipationKey)

        raise UnexpectedStatusError(response.status_code, response.text)

    def delete_participation_key_by_id(
        self,
        participation_id: str,
    ) -> None:
        """
        Delete a given participation key by ID
        """

        path = "/v2/participation/{participation-id}"
        path = path.replace("{participation-id}", str(participation_id))

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def generate_participation_keys(
        self,
        address: str,
        first: int,
        last: int,
        *,
        dilution: int | None = None,
    ) -> str:
        """
        Generate and install participation keys to the node.
        """

        path = "/v2/participation/generate/{address}"
        path = path.replace("{address}", str(address))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if dilution is not None:
            params["dilution"] = dilution

        if first is not None:
            params["first"] = first

        if last is not None:
            params["last"] = last

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, type_=str)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_config(
        self,
    ) -> str:
        """
        Gets the merged config file.
        """

        path = "/debug/settings/config"
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

    def get_debug_settings_prof(
        self,
    ) -> models.AlgodMutexAndBlockingProfilingState:
        """
        Retrieves the current settings for blocking and mutex profiles
        """

        path = "/debug/settings/pprof"
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
            return self._decode_response(response, model=models.AlgodMutexAndBlockingProfilingState)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_participation_key_by_id(
        self,
        participation_id: str,
    ) -> models.ParticipationKey:
        """
        Get participation key info given a participation ID
        """

        path = "/v2/participation/{participation-id}"
        path = path.replace("{participation-id}", str(participation_id))

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
            return self._decode_response(response, model=models.ParticipationKey)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_participation_keys(
        self,
    ) -> list[models.ParticipationKey]:
        """
        Return a list of participation keys
        """

        path = "/v2/participation"
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
            return self._decode_response(response, list_model=models.ParticipationKey)

        raise UnexpectedStatusError(response.status_code, response.text)

    def put_debug_settings_prof(
        self,
    ) -> models.AlgodMutexAndBlockingProfilingState:
        """
        Enables blocking and mutex profiles, and returns the old settings
        """

        path = "/debug/settings/pprof"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "PUT",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.AlgodMutexAndBlockingProfilingState)

        raise UnexpectedStatusError(response.status_code, response.text)

    def shutdown_node(
        self,
        *,
        timeout: int | None = None,
    ) -> dict[str, object]:
        """
        Special management endpoint to shutdown the node. Optionally provide a timeout parameter
        to indicate that the node should begin shutting down after a number of seconds.
        """

        path = "/v2/shutdown"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if timeout is not None:
            params["timeout"] = timeout

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, type_=dict[str, object])

        raise UnexpectedStatusError(response.status_code, response.text)

    def start_catchup(
        self,
        catchpoint: str,
        *,
        min_: int | None = None,
    ) -> models.StartCatchupResponseModel:
        """
        Starts a catchpoint catchup.
        """

        path = "/v2/catchup/{catchpoint}"
        path = path.replace("{catchpoint}", str(catchpoint))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()
        if min_ is not None:
            params["min"] = min_

        accept_value: str | None = None

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "POST",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.StartCatchupResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    # public

    def account_application_information(
        self,
        address: str,
        application_id: int,
        *,
        response_format: Literal["json", "msgpack"] | None = None,
    ) -> models.AccountApplicationInformationResponseModel:
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

        if selected_format is not None:
            params["format"] = selected_format
            if selected_format == "msgpack":
                accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.AccountApplicationInformationResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def account_asset_information(
        self,
        address: str,
        asset_id: int,
    ) -> models.AccountAssetInformationResponseModel:
        """
        Get account information about a given asset.
        """

        path = "/v2/accounts/{address}/assets/{asset-id}"
        path = path.replace("{address}", str(address))

        path = path.replace("{asset-id}", str(asset_id))

        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        params["format"] = "json"

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.AccountAssetInformationResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def account_assets_information(
        self,
        address: str,
        *,
        limit: int | None = None,
        next_: str | None = None,
    ) -> models.AccountAssetsInformationResponseModel:
        """
        Get a list of assets held by an account, inclusive of asset params.
        """

        path = "/v2/accounts/{address}/assets"
        path = path.replace("{address}", str(address))

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
            return self._decode_response(response, model=models.AccountAssetsInformationResponseModel)

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

        params["format"] = "json"

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Account)

        raise UnexpectedStatusError(response.status_code, response.text)

    def experimental_check(
        self,
    ) -> None:
        """
        Returns OK if experimental API is enabled.
        """

        path = "/v2/experimental"
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
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_application_box_by_name(
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

    def get_application_boxes(
        self,
        application_id: int,
        *,
        max_: int | None = None,
    ) -> models.GetApplicationBoxesResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetApplicationBoxesResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_application_by_id(
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Application)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_asset_by_id(
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.Asset)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_block(
        self,
        round_: int,
        *,
        header_only: bool | None = None,
    ) -> models.GetBlock:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetBlock)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_block_hash(
        self,
        round_: int,
    ) -> models.GetBlockHashResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetBlockHashResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_block_logs(
        self,
        round_: int,
    ) -> models.GetBlockLogsResponseModel:
        """
        Get all of the logs from outer and inner app calls in the given round
        """

        path = "/v2/blocks/{round}/logs"
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetBlockLogsResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_block_time_stamp_offset(
        self,
    ) -> models.GetBlockTimeStampOffsetResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetBlockTimeStampOffsetResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_block_tx_ids(
        self,
        round_: int,
    ) -> models.GetBlockTxIdsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetBlockTxIdsResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_genesis(
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GenesisFileInJson)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_ledger_state_delta(
        self,
        round_: int,
    ) -> bytes:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, raw_msgpack=True)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_ledger_state_delta_for_transaction_group(
        self,
        id_: str,
    ) -> bytes:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, raw_msgpack=True)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_light_block_header_proof(
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.LightBlockHeaderProof)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_pending_transactions(
        self,
        *,
        max_: int | None = None,
    ) -> models.GetPendingTransactionsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetPendingTransactionsResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_pending_transactions_by_address(
        self,
        address: str,
        *,
        max_: int | None = None,
    ) -> models.GetPendingTransactionsByAddressResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetPendingTransactionsByAddressResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_ready(
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_state_proof(
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.StateProof)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_status(
        self,
    ) -> models.GetStatusResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetStatusResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_supply(
        self,
    ) -> models.GetSupplyResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetSupplyResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_sync_round(
        self,
    ) -> models.GetSyncRoundResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.GetSyncRoundResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_transaction_group_ledger_state_deltas_for_round(
        self,
        round_: int,
    ) -> bytes:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, raw_msgpack=True)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_transaction_proof(
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

        if selected_format is not None:
            params["format"] = selected_format
            if selected_format == "msgpack":
                accept_value = "application/msgpack"

        headers.setdefault("accept", accept_value or "application/json")
        request_kwargs: dict[str, Any] = {
            "method": "GET",
            "url": path,
            "params": params,
            "headers": headers,
        }

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TransactionProof)

        raise UnexpectedStatusError(response.status_code, response.text)

    def get_version(
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.VersionContainsTheCurrentAlgodVersion)

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def metrics(
        self,
    ) -> None:
        """
        Return metrics about algod functioning.
        """

        path = "/metrics"
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
            return

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.PendingTransactionResponse)

        raise UnexpectedStatusError(response.status_code, response.text)

    def raw_transaction(
        self,
        body: bytes,
    ) -> models.RawTransactionResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.RawTransactionResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def raw_transaction_async(
        self,
        body: bytes,
    ) -> None:
        """
        Fast track for broadcasting a raw transaction or transaction group to the network
        through the tx handler without performing most of the checks and reporting detailed
        errors. Should be only used for development and performance testing.
        """

        path = "/v2/transactions/async"
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

        response = self._client.request(**request_kwargs)
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

        response = self._client.request(**request_kwargs)
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def simulate_transaction(
        self,
        body: models.SimulateRequest,
    ) -> models.SimulateTransactionResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.SimulateTransactionResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def swagger_json(
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

    def teal_compile(
        self,
        body: bytes,
        *,
        sourcemap: bool | None = None,
    ) -> models.TealCompileResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TealCompileResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def teal_disassemble(
        self,
        body: bytes,
    ) -> models.TealDisassembleResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TealDisassembleResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def teal_dryrun(
        self,
        *,
        body: models.DryrunRequest | None = None,
    ) -> models.TealDryrunResponseModel:
        """
        Provide debugging information for a transaction (or group).
        """

        path = "/v2/teal/dryrun"
        params: dict[str, Any] = {}
        headers: Headers = self._config.resolve_headers()

        accept_value: str | None = None

        body_media_types = ["application/json", "application/msgpack"]

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
                    "model": "DryrunRequest",
                },
                body_media_types,
            )

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TealDryrunResponseModel)

        raise UnexpectedStatusError(response.status_code, response.text)

    def transaction_params(
        self,
    ) -> models.TransactionParamsResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.TransactionParamsResponseModel)

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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return

        raise UnexpectedStatusError(response.status_code, response.text)

    def wait_for_block(
        self,
        round_: int,
    ) -> models.WaitForBlockResponseModel:
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

        response = self._client.request(**request_kwargs)
        if response.is_success:
            return self._decode_response(response, model=models.WaitForBlockResponseModel)

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
                return key.decode("utf-8")
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
