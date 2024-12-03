# from dataclasses import dataclass
# from typing import Any

# from algokit_utils._legacy_v2.application_specification import ApplicationSpecification
# from algokit_utils.models.account import Account


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


# @dataclass
# class AppDeployer:
#     app_manager: Any  # AppManager
#     transaction_sender: Any  # AlgorandClientTransactionSender
#     indexer: Any | None = None  # Indexer

#     def __post_init__(self):
#         self._app_lookups = {}

#     def deploy(self, deployment: dict[str, Any]):
#         metadata = deployment["metadata"]
#         deploy_time_params = deployment.get("deploy_time_params")
#         on_schema_break = deployment.get("on_schema_break")
#         on_update = deployment.get("on_update")
#         create_params = deployment["create_params"]
#         update_params = deployment["update_params"]
#         delete_params = deployment["delete_params"]
#         existing_deployments = deployment.get("existing_deployments")
#         ignore_cache = deployment.get("ignore_cache", False)
#         send_params = {
#             k: v
#             for k, v in deployment.items()
#             if k
#             not in {
#                 "metadata",
#                 "deploy_time_params",
#                 "on_schema_break",
#                 "on_update",
#                 "create_params",
#                 "update_params",
#                 "delete_params",
#                 "existing_deployments",
#                 "ignore_cache",
#             }
#         }

#         create_params["note"] = update_params["note"] = TransactionComposer.arc2_note(
#             dapp_name="ALGOKIT_DEPLOYER", data=metadata, format="j"
#         )

#         if existing_deployments and existing_deployments["creator"] != create_params["sender"]:
#             raise ValueError("Invalid existingDeployments creator")

#         if not existing_deployments and not self.indexer:
#             raise ValueError("Need indexer or existingDeployments")

#         apps = existing_deployments or self.get_creator_apps_by_name(create_params["sender"], ignore_cache)
#         existing_app = apps["apps"].get(metadata["name"])

#         if not existing_app or existing_app["deleted"]:
#             return self._create_app(create_params, metadata, send_params)

#         return self._handle_existing_app(
#             existing_app, create_params, update_params, delete_params, metadata, on_schema_break, on_update, send_params
#         )

#     def get_creator_apps_by_name(self, creator_address: str | Account, ignore_cache: bool = False):
#         if isinstance(creator_address, Account):
#             creator_address = creator_address.address

#         if not ignore_cache and creator_address in self._app_lookups:
#             return self._app_lookups[creator_address]

#         if not self.indexer:
#             raise ValueError("Need indexer for getCreatorApps")

#         app_lookup = {}
#         # Implementation of lookup logic here

#         lookup = {"creator": creator_address, "apps": app_lookup}

#         self._app_lookups[creator_address] = lookup
#         return lookup

#     def _create_app(self, create_params, metadata, send_params):
#         # Implementation of app creation
#         pass

#     def _handle_existing_app(
#         self,
#         existing_app,
#         create_params,
#         update_params,
#         delete_params,
#         metadata,
#         on_schema_break,
#         on_update,
#         send_params,
#     ):
#         # Implementation of handling existing app
#         pass

#     def _update_app_lookup(self, sender: str, app_metadata: dict[str, Any]):
#         lookup = self._app_lookups.get(sender, {"creator": sender, "apps": {}})
#         lookup["apps"][app_metadata["name"]] = app_metadata
#         self._app_lookups[sender] = lookup
