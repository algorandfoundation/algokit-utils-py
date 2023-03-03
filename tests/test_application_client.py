from pathlib import Path
from uuid import uuid4

import algokit_utils.deployer
from algokit_utils import ApplicationClient
from algokit_utils.application_specification import ApplicationSpecification


class GeneratedCounterClient:
    def __init__(self, client: ApplicationClient):
        self._client = client

    def increment(self) -> int:
        return self._client.call("increment").return_value

    def decrement(self) -> int:
        return self._client.call("decrement").return_value


def _read_spec(path: str) -> ApplicationSpecification:
    return ApplicationSpecification.from_json(Path(path).read_text(encoding="utf-8"))


V1_spec = _read_spec("helloworld_application_v1.json")
V2_spec = _read_spec("helloworld_application_v2.json")
V3_spec = _read_spec("counter_application.json")
# pretend these app specs are all different versions of the "same" app
V2_spec.contract.name = V1_spec.contract.name
V3_spec.contract.name = V1_spec.contract.name


def get_unique_name() -> str:
    name = str(uuid4()).replace("-", "")
    assert name.isalnum()
    return name


def test_deploy_new():
    algod_client = algokit_utils.deployer.get_algod_client()
    indexer = algokit_utils.deployer.get_indexer_client()
    algokit_utils.deployer.get_indexer_client()
    creator = algokit_utils.deployer.get_account(algod_client, get_unique_name())

    app = algokit_utils.deployer.deploy_app(algod_client, indexer, V1_spec, creator, version="1.0")
    # TODO: better assert
    assert app.id


def test_deploy_new_then_update():
    algod_client = algokit_utils.deployer.get_algod_client()
    indexer = algokit_utils.deployer.get_indexer_client()
    algokit_utils.deployer.get_indexer_client()
    creator = algokit_utils.deployer.get_account(algod_client, get_unique_name())

    app_v1 = algokit_utils.deployer.deploy_app(algod_client, indexer, V1_spec, creator, version="1.0")
    assert app_v1.id

    app_v2 = algokit_utils.deployer.deploy_app(algod_client, indexer, V2_spec, creator, version="2.0")
    # TODO: better assert
    assert app_v2.id != app_v1.id


def test_deploy_new_then_update_with_delete_on_update():
    algod_client = algokit_utils.deployer.get_algod_client()
    indexer = algokit_utils.deployer.get_indexer_client()
    algokit_utils.deployer.get_indexer_client()
    creator = algokit_utils.deployer.get_account(algod_client, get_unique_name())

    app_v1 = algokit_utils.deployer.deploy_app(algod_client, indexer, V1_spec, creator, version="1.0")
    assert app_v1.id

    app_v2 = algokit_utils.deployer.deploy_app(
        algod_client, indexer, V2_spec, creator, version="2.0", delete_app_on_update_if_exists=True
    )
    # TODO: better assert
    assert app_v2.id != app_v1.id


# scenarios
# create v1
# create v1, update v2
# create v1, update v2, delete on update = true
# create v1, update v2, delete on update = false
# create v1, update v3 (schema change), delete on schema break = true
# create v1, update v3 (schema change), delete on schema break = false


def _interact_with_counter(api: GeneratedCounterClient):
    api.increment()
    api.increment()
    api.increment()
    result = api.increment()
    print(f"Current counter value: {result}")

    result = api.decrement()
    print(f"Current counter value: {result}")
