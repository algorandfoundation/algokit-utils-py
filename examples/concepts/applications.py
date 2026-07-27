"""Demonstrates creating a minimal application from raw TEAL and reading it back.

This maps to the Concepts -> Applications docs page. It uses a trivial inline
TEAL program so it has no dependency on compiled contract artifacts. Real
projects would use ``AppFactory`` / ``AppClient`` with an ARC-56 app spec.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.applications``.
"""

from algokit_utils import AppCreateParams
from examples._helpers import setup_localnet_environment

# Smallest valid programs: approve everything.
APPROVAL_TEAL = "#pragma version 12\nint 1"
CLEAR_STATE_TEAL = "#pragma version 12\nint 1"


def main() -> None:
    env = setup_localnet_environment()
    algorand, account_a, _ = env

    # example: CREATE_APP
    create_result = algorand.send.app_create(
        AppCreateParams(
            sender=account_a.address,
            approval_program=APPROVAL_TEAL,
            clear_state_program=CLEAR_STATE_TEAL,
        )
    )
    app_id = create_result.app_id
    # example: CREATE_APP

    # example: READ_APP
    app_info = algorand.app.get_by_id(app_id)
    print(f"App {app_info.app_id} created at address {app_info.app_address}")
    # example: READ_APP

    assert app_info.app_id == app_id
    assert app_info.creator == account_a.address


if __name__ == "__main__":
    main()
