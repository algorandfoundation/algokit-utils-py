# from pathlib import Path

# import pytest

# from algokit_utils.applications.app_factory import AppFactory, AppFactoryDeployParams
# from algokit_utils.clients.algorand_client import AlgorandClient
# from algokit_utils.models.account import Account


# @pytest.fixture
# def algorand(funded_account: Account) -> AlgorandClient:
#     client = AlgorandClient.default_local_net()
#     client.set_signer(sender=funded_account.address, signer=funded_account.signer)
#     return client


# @pytest.fixture
# def factory(algorand: AlgorandClient, funded_account: Account) -> AppFactory:
#     """Create AppFactory fixture"""
#     raw_arc56_spec = (Path(__file__).parent.parent / "artifacts" / "hello_world" / "arc32_app_spec.json").read_text()
#     return algorand.client.get_app_factory(app_spec=raw_arc56_spec, default_sender=funded_account.address)


# class TestARC56:
#     def test_error_messages_with_template_vars(self, factory: AppFactory) -> None:
#         """Test ARC56 error messages with dynamic template variables"""
#         # Deploy app
#         result = factory.deploy(
#             AppFactoryDeployParams(
#                 create_params={"method": "createApplication"},
#                 deploy_time_params={
#                     "bytes64TmplVar": "0" * 64,
#                     "uint64TmplVar": 123,
#                     "bytes32TmplVar": "0" * 32,
#                     "bytesTmplVar": "foo",
#                 },
#             )
#         )
#         app_client = result.app_client

#         # Test error handling
#         with pytest.raises(Exception) as exc:
#             app_client.call(method="throwError")

#         assert "this is an error" in str(exc.value)

#     def test_undefined_error_message(self, factory: AppFactory) -> None:
#         """Test ARC56 undefined error message with template variables"""
#         # Deploy app
#         result = factory.deploy(
#             create_params={"method": "createApplication"},
#             deploy_time_params={
#                 "bytes64TmplVar": "0" * 64,
#                 "uint64TmplVar": 0,
#                 "bytes32TmplVar": "0" * 32,
#                 "bytesTmplVar": "foo",
#             },
#         )
#         app_id = result.app_id

#         # Create new client without source maps
#         app_client = AppClient(
#             app_id=app_id, algod=algod, app_spec=arc56_json, default_sender=get_localnet_default_account()
#         )

#         # Test error handling
#         with pytest.raises(Exception) as exc:
#             app_client.call(method="tmpl")

#         error_stack = "\n".join(line.strip() for line in str(exc.value).split("\n"))
#         assert "assert <--- Error" in error_stack
#         assert "intc 1 // TMPL_uint64TmplVar" in error_stack
