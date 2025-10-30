def test_module_exists() -> None:
    import algokit_algod_client

    assert algokit_algod_client, "module should exist"
