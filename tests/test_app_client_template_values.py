from typing import TYPE_CHECKING

import algokit_utils
import pytest

from tests.conftest import get_unique_name, read_spec

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient
    from algosdk.v2client.indexer import IndexerClient


def test_create_with_all_template_values_on_initialize(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: algokit_utils.Account,
) -> None:
    app_spec = read_spec("app_client_test.json")
    client = algokit_utils.ApplicationClient(
        algod_client,
        app_spec,
        creator=funded_account,
        indexer_client=indexer_client,
        template_values={"VERSION": 1, "UPDATABLE": 1, "DELETABLE": 1},
        app_name=get_unique_name(),
    )
    client.create("create")

    assert client.call("version").return_value == 1


def test_create_with_some_template_values_on_initialize(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: algokit_utils.Account,
) -> None:
    app_spec = read_spec("app_client_test.json")
    client = algokit_utils.ApplicationClient(
        algod_client,
        app_spec,
        creator=funded_account,
        indexer_client=indexer_client,
        template_values={
            "VERSION": 1,
        },
        app_name=get_unique_name(),
    )

    with pytest.raises(
        expected_exception=algokit_utils.DeploymentFailedError,
        match=r"allow_update must be specified if deploy time configuration of update is being used",
    ):
        client.create("create")


def test_deploy_with_some_template_values_on_initialize(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: algokit_utils.Account,
) -> None:
    app_spec = read_spec("app_client_test.json")
    client = algokit_utils.ApplicationClient(
        algod_client,
        app_spec,
        creator=funded_account,
        indexer_client=indexer_client,
        template_values={
            "VERSION": 1,
        },
        app_name=get_unique_name(),
    )

    client.deploy(allow_delete=True, allow_update=True, create_args=algokit_utils.ABICreateCallArgs(method="create"))
    assert client.call("version").return_value == 1


def test_deploy_with_overriden_template_values(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: algokit_utils.Account,
) -> None:
    app_spec = read_spec("app_client_test.json")
    client = algokit_utils.ApplicationClient(
        algod_client,
        app_spec,
        creator=funded_account,
        indexer_client=indexer_client,
        template_values={
            "VERSION": 1,
        },
        app_name=get_unique_name(),
    )

    new_version = 2
    client.deploy(
        allow_delete=True,
        allow_update=True,
        template_values={"VERSION": new_version},
        create_args=algokit_utils.ABICreateCallArgs(method="create"),
    )
    assert client.call("version").return_value == new_version


def test_deploy_with_no_initialize_template_values(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: algokit_utils.Account,
) -> None:
    app_spec = read_spec("app_client_test.json")
    client = algokit_utils.ApplicationClient(
        algod_client,
        app_spec,
        creator=funded_account,
        indexer_client=indexer_client,
        app_name=get_unique_name(),
    )

    new_version = 3
    client.deploy(
        allow_delete=True,
        allow_update=True,
        template_values={"VERSION": new_version},
        create_args=algokit_utils.ABICreateCallArgs(method="create"),
    )
    assert client.call("version").return_value == new_version


def test_deploy_with_missing_template_values(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: algokit_utils.Account,
) -> None:
    app_spec = read_spec("app_client_test.json")
    client = algokit_utils.ApplicationClient(
        algod_client,
        app_spec,
        creator=funded_account,
        indexer_client=indexer_client,
        app_name=get_unique_name(),
    )

    with pytest.raises(
        expected_exception=algokit_utils.DeploymentFailedError,
        match=r"The following template values were not provided: TMPL_VERSION",
    ):
        client.deploy(
            allow_delete=True, allow_update=True, create_args=algokit_utils.ABICreateCallArgs(method="create")
        )


def test_deploy_with_multi_underscore_template_value(
    algod_client: "AlgodClient",
    indexer_client: "IndexerClient",
    funded_account: algokit_utils.Account,
) -> None:
    from tests.app_multi_underscore_template_var import app

    some_value = 123
    app_spec = app.build(algod_client)
    client = algokit_utils.ApplicationClient(
        algod_client,
        app_spec,
        creator=funded_account,
        indexer_client=indexer_client,
        app_name=get_unique_name(),
        template_values={"SOME_VALUE": some_value},
    )

    client.deploy(allow_update=True, allow_delete=True)
    result = client.call("some_value")
    assert result.return_value == some_value
