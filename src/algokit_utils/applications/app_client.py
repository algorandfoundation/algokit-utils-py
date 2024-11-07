from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import algosdk
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.logic import get_application_address
from algosdk.source_map import SourceMap
from algosdk.transaction import OnComplete

from algokit_utils._legacy_v2.models import (
    ABIValue,
    AppState,
    TransactionResponse,
)
from algokit_utils.applications.app_manager import BoxName
from algokit_utils.models.abi import Arc56Contract
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.models.application import ApplicationSpecification
from algokit_utils.protocols.application import AlgorandClientProtocol
from algokit_utils.transactions.transaction_composer import PaymentParams, TransactionComposer


@dataclass
class AppClientParams:
    app_id: int
    app_spec: Arc56Contract | ApplicationSpecification | str
    algorand: AlgorandClientProtocol
    app_name: str | None = None
    default_sender: str | None = None
    default_signer: TransactionSigner | None = None
    approval_source_map: SourceMap | None = None
    clear_source_map: SourceMap | None = None


@dataclass
class AppClientCompilationParams:
    deploy_time_params: dict[str, Any] | None = None
    updatable: bool | None = None
    deletable: bool | None = None


@dataclass
class AppClientCallParams:
    sender: str | None = None
    signer: TransactionSigner | None = None
    note: bytes | None = None
    send_params: dict[str, Any] | None = None
    args: dict[str, Any] | None = None
    method: str | None = None
    on_complete: OnComplete | None = None


class AppClient:
    def __init__(self, params: AppClientParams) -> None:
        self._app_id = params.app_id
        self._app_spec = self.normalize_app_spec(params.app_spec)
        self._algorand = params.algorand
        self._app_name = params.app_name or self._app_spec.name
        self._default_sender = params.default_sender
        self._default_signer = params.default_signer
        self._approval_source_map = params.approval_source_map
        self._clear_source_map = params.clear_source_map
        self._app_address = get_application_address(self._app_id)

    @staticmethod
    def normalize_app_spec(app_spec: Arc56Contract | ApplicationSpecification | str) -> Arc56Contract:
        if isinstance(app_spec, str):
            spec = json.loads(app_spec)
        else:
            spec = app_spec

        if isinstance(spec, Arc56Contract):
            return spec
        elif isinstance(spec, ApplicationSpecification):
            # Convert ARC-32 to ARC-56
            from algokit_utils.applications.utils import arc32_to_arc56

            return arc32_to_arc56(spec)
        elif isinstance(spec, dict):
            return Arc56Contract(**spec)
        else:
            raise ValueError("Invalid app spec format")

    @property
    def app_id(self) -> int:
        return self._app_id

    @property
    def app_address(self) -> str:
        return self._app_address

    @property
    def app_name(self) -> str:
        return self._app_name

    @property
    def app_spec(self) -> Arc56Contract:
        return self._app_spec

    @property
    def algorand(self) -> AlgorandClientProtocol:
        return self._algorand

    def clone(self, **params: Any) -> AppClient:
        return AppClient(
            AppClientParams(
                app_id=params.get("app_id", self._app_id),
                app_spec=self._app_spec,
                algorand=self.algorand,
                app_name=params.get("app_name", self._app_name),
                default_sender=params.get("default_sender", self._default_sender),
                default_signer=params.get("default_signer", self._default_signer),
                approval_source_map=params.get("approval_source_map", self._approval_source_map),
                clear_source_map=params.get("clear_source_map", self._clear_source_map),
            )
        )

    def new_group(self) -> TransactionComposer:
        return self.algorand.new_group()

    def _get_sender(self, sender: str | None = None) -> str:
        if not sender and not self._default_sender:
            raise ValueError(
                f"No sender provided and no default sender present in app client for call to app {self._app_name}"
            )
        return sender or self._default_sender  # type: ignore[return-value]

    def _get_signer(
        self,
        sender: str | None,
        signer: TransactionSigner | None,
    ) -> TransactionSigner | None:
        return signer or (None if sender else self._default_signer)

    def fund_app_account(self, amount: AlgoAmount, params: AppClientCallParams | None = None) -> None:
        sender = self._get_sender(params.sender if params else None)
        signer = self._get_signer(sender, params.signer if params else None)
        payment_params = PaymentParams(
            sender=sender,
            signer=signer,
            receiver=self.app_address,
            amount=amount,
            note=params.note if params else None,
            **(params.send_params if params and params.send_params else {}),
        )
        self._algorand.send.payment(payment_params)

    def get_global_state(self) -> AppState:
        return self._algorand.app.get_global_state(self.app_id)

    def get_local_state(self, address: str) -> AppState:
        return self._algorand.app.get_local_state(self.app_id, address)

    def get_box_names(self) -> list[BoxName]:
        return self._algorand.app.get_box_names(self.app_id)

    def get_box_value(self, name: bytes) -> bytes:
        return self._algorand.app.get_box_value(self.app_id, name)

    def get_box_value_from_abi_type(self, name: bytes, abi_type: algosdk.abi.ABIType) -> ABIValue:
        return self._algorand.app.get_box_value_from_abi_type(self.app_id, name, abi_type)

    def compile(self, params: AppClientCompilationParams | None = None) -> None:
        # Implement compilation logic here
        pass

    def create(self, params: AppClientCallParams | None = None) -> TransactionResponse:
        # Implement create logic here
        pass

    def update(self, params: AppClientCallParams | None = None) -> TransactionResponse:
        # Implement update logic here
        pass

    def delete(self, params: AppClientCallParams | None = None) -> TransactionResponse:
        # Implement delete logic here
        pass

    def call(self, params: AppClientCallParams | None = None) -> Any:
        # Implement call logic here
        pass

    def _handle_call_errors(self, call: Callable[[], Awaitable[Any]]) -> Any:
        try:
            return call()
        except Exception as e:
            raise self._expose_logic_error(e)

    def _expose_logic_error(self, e: Exception) -> Exception:
        # Implement logic error exposure, possibly augmenting the exception with debugging info
        return e

    def get_abi_methods(self) -> list[dict[str, Any]]:
        return self._app_spec.contract.methods

    def process_method_call_return(self, result: Any, method: Any) -> Any:
        # Process the result of an ABI method call
        pass

    def get_state_methods(self):
        def get_all():
            state = self.get_global_state()
            keys = self._app_spec.state.keys["global"]
            result = {}
            for key in keys:
                result[key] = get_value(key, state)
            return result

        def get_value(name: str, state: AppState | None = None):
            state = state or self.get_global_state()
            key_info = self._app_spec.state.keys["global"][name]
            value = state.get(key_info["key"])
            if value is not None:
                return value  # Decode using ABI if necessary
            return None

        def get_map_value(map_name: str, key: Any, state: AppState | None = None):
            state = state or self.get_global_state()
            map_info = self._app_spec.state.maps["global"][map_name]
            full_key = map_info["prefix"] + key
            value = state.get(full_key)
            if value is not None:
                return value  # Decode using ABI if necessary
            return None

        def get_map(map_name: str):
            state = self.get_global_state()
            map_info = self._app_spec.state.maps["global"][map_name]
            result = {}
            for key, value in state.items():
                if key.startswith(map_info["prefix"]):
                    map_key = key[len(map_info["prefix"]) :]
                    result[map_key] = value  # Decode using ABI if necessary
            return result

        return {
            "get_all": get_all,
            "get_value": get_value,
            "get_map_value": get_map_value,
            "get_map": get_map,
        }
