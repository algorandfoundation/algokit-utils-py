"""Demonstrates the failure path — logic errors with TEAL source context,
source-map reuse, error transformers, and the debug configuration that emits
traces for the AlgoKit AVM Debugger.

This maps to the Concepts -> Errors & Debugging docs page. The failing calls
use the `State` test contract (examples/artifacts/State.arc56.json), whose
`error` method always asserts.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.errors_and_debugging``.
"""

import logging
import shutil
import tempfile
from pathlib import Path

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AppClient,
    AppClientMethodCallParams,
    LogicError,
    PaymentParams,
    SigningAccount,
)
from algokit_utils.config import config
from examples._helpers import setup_localnet_environment


def inspect_logic_error(algorand: AlgorandClient, deployer: SigningAccount) -> AppClient:
    # example: INSPECT_LOGIC_ERROR
    from algokit_utils import AppClientMethodCallParams, LogicError

    # Clients created through a factory hold the TEAL source map from compilation
    app_spec = Path("examples/artifacts/State.arc56.json").read_text()
    factory = algorand.client.get_app_factory(app_spec=app_spec, default_sender=deployer.address)
    app_client, _ = factory.deploy(
        compilation_params={"deploy_time_params": {"VALUE": 1}, "updatable": True, "deletable": True},
    )

    try:
        app_client.send.call(AppClientMethodCallParams(method="error"))
    except LogicError as e:
        # The fields locate the failure in the decoded TEAL program
        print(f"Transaction {e.transaction_id} failed at PC {e.pc}, TEAL line {e.line_no}")
        # str(e) renders the failing line in context with an <-- Error marker
        print(e)
    # example: INSPECT_LOGIC_ERROR
    return app_client


def reuse_source_maps(algorand: AlgorandClient, deployer: SigningAccount, app_client: AppClient) -> None:
    # example: EXPORT_IMPORT_SOURCE_MAPS
    # A client constructed by app ID holds no source maps of its own
    fresh_client = algorand.client.get_app_client_by_id(
        app_spec=Path("examples/artifacts/State.arc56.json").read_text(),
        app_id=app_client.app_id,
        default_sender=deployer.address,
    )

    # Export from the client that compiled the app, import onto the fresh one
    source_maps = app_client.export_source_maps()
    fresh_client.import_source_maps(source_maps)
    # example: EXPORT_IMPORT_SOURCE_MAPS

    located = False
    try:
        fresh_client.send.call(AppClientMethodCallParams(method="error"))
    except LogicError as e:
        located = e.line_no is not None
    assert located, "imported source maps should re-enable TEAL line resolution"


def transform_errors(algorand: AlgorandClient, funder: SigningAccount) -> None:
    # An account funded below the payment amount makes algod report an overspend
    poor_account = algorand.account.random()
    algorand.send.payment(
        PaymentParams(sender=funder.address, receiver=poor_account.address, amount=AlgoAmount(micro_algo=200_000))
    )

    # example: REGISTER_ERROR_TRANSFORMER
    class InsufficientFundsError(Exception):
        pass

    def to_domain_error(error: Exception) -> Exception:
        # Return a new exception to replace the error, or the original to leave it unchanged
        if "overspend" in str(error):
            return InsufficientFundsError("the sender cannot cover the payment amount")
        return error

    algorand.register_error_transformer(to_domain_error)

    try:
        algorand.send.payment(
            PaymentParams(sender=poor_account.address, receiver=funder.address, amount=AlgoAmount(algo=1))
        )
    except InsufficientFundsError as e:
        print(f"Transformed: {e}")
    # example: REGISTER_ERROR_TRANSFORMER
    algorand.unregister_error_transformer(to_domain_error)


def capture_traces(algorand: AlgorandClient, sender: SigningAccount, receiver: SigningAccount) -> None:
    debug_root = Path(tempfile.mkdtemp())
    try:
        # example: CONFIGURE_DEBUG
        from algokit_utils.config import config

        # debug switches on trace and source-map emission;
        # project_root is where the artifacts are written, auto-detected in AlgoKit projects;
        # trace_all extends tracing from failed sends to every send
        config.configure(debug=True, project_root=debug_root, trace_all=True)
        # example: CONFIGURE_DEBUG

        algorand.send.payment(
            PaymentParams(sender=sender.address, receiver=receiver.address, amount=AlgoAmount(algo=1), note=b"traced")
        )
        trace_files = list((debug_root / "debug_traces").glob("*.trace.avm.json"))
        assert trace_files, "expected the traced send to write a trace file"
    finally:
        shutil.rmtree(debug_root, ignore_errors=True)


def restore_config_defaults(original_project_root: Path | None) -> None:
    # debug and project_root are left unchanged when omitted, so debug must be reset explicitly
    config.configure(
        debug=False,
        trace_all=False,
        trace_buffer_size_mb=256,
        max_search_depth=10,
        populate_app_call_resources=True,
    )
    # configure() cannot reset project_root to None, so restore it directly
    config._project_root = original_project_root  # noqa: SLF001
    config.logger.setLevel(logging.NOTSET)
    assert config.debug is False
    assert config.trace_all is False
    assert config.project_root == original_project_root


def main() -> None:
    env = setup_localnet_environment()
    algorand = env.algorand
    deployer = env.account_a

    original_project_root = config.project_root
    try:
        app_client = inspect_logic_error(algorand, deployer)
        reuse_source_maps(algorand, deployer, app_client)
        transform_errors(algorand, deployer)
        capture_traces(algorand, deployer, env.account_b)
    finally:
        restore_config_defaults(original_project_root)


if __name__ == "__main__":
    main()
