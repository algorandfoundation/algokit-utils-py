import json

import pytest
from algokit_utils.dispenser_api import (
    DISPENSER_ASSETS,
    DispenserApiConfig,
    DispenserApiTestnetClient,
    DispenserAssetName,
)
from pytest_httpx import HTTPXMock


class TestDispenserApiTestnetClient:
    def test_fund_account_with_algos_with_auth_token(self, httpx_mock: HTTPXMock) -> None:
        mock_response = {"txID": "dummy_tx_id", "amount": 1}
        httpx_mock.add_response(
            url=f"{DispenserApiConfig.BASE_URL}/fund/{DispenserAssetName.ALGO}",
            method="POST",
            json=mock_response,
        )
        dispenser_client = DispenserApiTestnetClient(auth_token="dummy_auth_token")
        address = "dummy_address"
        amount = 1
        asset_id = DispenserAssetName.ALGO
        response = dispenser_client.fund(address, amount, asset_id)
        assert response.tx_id == "dummy_tx_id"
        assert response.amount == 1

    def test_register_refund_with_auth_token(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{DispenserApiConfig.BASE_URL}/refund",
            method="POST",
            json={},
        )
        dispenser_client = DispenserApiTestnetClient(auth_token="dummy_auth_token")
        refund_txn_id = "dummy_txn_id"
        dispenser_client.refund(refund_txn_id)
        assert len(httpx_mock.get_requests()) == 1
        request = httpx_mock.get_requests()[0]
        assert request.method == "POST"
        assert request.url.path == "/refund"
        assert request.headers["Authorization"] == f"Bearer {dispenser_client.auth_token}"
        assert json.loads(request.read().decode()) == {"refundTransactionID": refund_txn_id}

    def test_limit_with_auth_token(self, httpx_mock: HTTPXMock) -> None:
        amount = 10000000
        mock_response = {"amount": amount}
        httpx_mock.add_response(
            url=f"{DispenserApiConfig.BASE_URL}/fund/{DISPENSER_ASSETS[DispenserAssetName.ALGO].asset_id}/limit",
            method="GET",
            json=mock_response,
        )
        dispenser_client = DispenserApiTestnetClient("dummy_auth_token")
        address = "dummy_address"
        response = dispenser_client.get_limit(address)
        assert response.amount == amount

    def test_dispenser_api_init(self) -> None:
        with pytest.raises(
            Exception,
            match="Can't init AlgoKit TestNet Dispenser API client because neither environment variable",
        ):
            DispenserApiTestnetClient()

    def test_dispenser_api_init_with_ci_(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALGOKIT_DISPENSER_ACCESS_TOKEN", "test_value")

        client = DispenserApiTestnetClient()
        assert client.auth_token == "test_value"

    def test_dispenser_api_init_with_ci_and_arg(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALGOKIT_DISPENSER_ACCESS_TOKEN", "test_value")

        client = DispenserApiTestnetClient("test_value_2")
        assert client.auth_token == "test_value_2"
