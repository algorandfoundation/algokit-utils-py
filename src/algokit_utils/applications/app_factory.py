# from dataclasses import dataclass
# from typing import Any

# from algokit_utils._legacy_v2.application_client import ApplicationClient
# from algokit_utils._legacy_v2.application_specification import ApplicationSpecification


# @dataclass
# class AppFactoryParams:
#     app_spec: ApplicationSpecification | str
#     algorand: Any  # AlgorandClient
#     app_name: str | None = None
#     default_sender: str | None = None
#     default_signer: Any | None = None  # TransactionSigner
#     version: str | None = None
#     updatable: bool | None = None
#     deletable: bool | None = None
#     deploy_time_params: dict[str, Any] | None = None


# class AppFactory:
#     def __init__(self, params: AppFactoryParams):
#         self._app_spec = ApplicationClient.normalise_app_spec(params.app_spec)
#         self._app_name = params.app_name or self._app_spec.name
#         self._algorand = params.algorand
#         self._version = params.version or "1.0"
#         self._default_sender = params.default_sender
#         self._default_signer = params.default_signer
#         self._deploy_time_params = params.deploy_time_params
#         self._updatable = params.updatable
#         self._deletable = params.deletable
#         self._approval_source_map = None
#         self._clear_source_map = None

#     @property
#     def app_name(self):
#         return self._app_name

#     @property
#     def app_spec(self):
#         return self._app_spec

#     @property
#     def algorand(self):
#         return self._algorand

#     def get_app_client_by_id(self, params: dict[str, Any]):
#         return ApplicationClient(
#             algod_client=self._algorand,
#             app_spec=self._app_spec,
#             app_id=params.get("app_id", 0),
#             app_name=params.get("app_name", self._app_name),
#             default_sender=params.get("default_sender", self._default_sender),
#             default_signer=params.get("default_signer", self._default_signer),
#             template_values=params.get("template_values"),
#         )

#     def get_app_client_by_creator_and_name(self, params: dict[str, Any]):
#         return ApplicationClient.from_creator_and_name(
#             algod_client=self._algorand,
#             app_spec=self._app_spec,
#             creator=params["creator"],
#             indexer_client=params.get("indexer_client"),
#             app_name=params.get("app_name", self._app_name),
#             default_sender=params.get("default_sender", self._default_sender),
#             template_values=params.get("template_values"),
#         )

#     def deploy(self, params: dict[str, Any]):
#         updatable = params.get("updatable", self._updatable)
#         deletable = params.get("deletable", self._deletable)
#         deploy_time_params = params.get("deploy_time_params", self._deploy_time_params)

#         app_client = self.get_app_client_by_id({})
#         return app_client.deploy(
#             version=params.get("version"),
#             signer=params.get("signer"),
#             sender=params.get("sender"),
#             allow_update=updatable,
#             allow_delete=deletable,
#             template_values=deploy_time_params,
#             create_args=params.get("create_args"),
#             update_args=params.get("update_args"),
#             delete_args=params.get("delete_args"),
#         )
