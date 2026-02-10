# ruff: noqa: N999, C901, PLR0912, PLR0915
"""
Example: Indexer Health Check

This example demonstrates how to check indexer health status using
the IndexerClient health_check() method.

Prerequisites:
- LocalNet running (via `algokit localnet start`)
"""

from shared import (
    create_indexer_client,
    print_error,
    print_header,
    print_info,
    print_step,
    print_success,
)


def main() -> None:
    print_header("Indexer Health Check Example")

    # Create an Indexer client connected to LocalNet
    indexer = create_indexer_client()

    # =========================================================================
    # Step 1: Perform Health Check
    # =========================================================================
    print_step(1, "Checking indexer health with health_check()")

    try:
        # health_check() returns a HealthCheck object with status information
        health = indexer.health_check()

        print_success("Indexer is healthy!")
        print_info("")
        print_info("Health check response:")
        print_info(f"  - version: {health.version}")
        print_info(f"  - db_available: {health.db_available}")
        print_info(f"  - is_migrating: {health.is_migrating}")
        print_info(f"  - message: {health.message}")
        print_info(f"  - round: {health.round_}")

        # Display errors if any
        if health.errors and len(health.errors) > 0:
            errors_str = ", ".join(health.errors)
            print_info(f"  - errors: {errors_str}")
        else:
            print_info("  - errors: none")

        # =========================================================================
        # Step 2: Interpret the Health Check Results
        # =========================================================================
        print_step(2, "Interpreting health check results")

        # Check if the database is available
        if health.db_available:
            print_success("Database is available and accessible")
        else:
            print_error("Database is NOT available")

        # Check if a migration is in progress
        if health.is_migrating:
            print_info("Note: Database migration is in progress")
            print_info("Some queries may be slower or unavailable during migration")
        else:
            print_success("No database migration in progress")

        # Display current round
        print_info(f"Indexer has processed blocks up to round {health.round_}")
    except Exception as e:
        print_error(f"Health check failed: {e}")
        print_info("")
        print_info("Common causes of health check failures:")
        print_info("  - Indexer service is not running")
        print_info("  - Network connectivity issues")
        print_info("  - Incorrect indexer URL or port")
        print_info("")
        print_info("To start LocalNet, run: algokit localnet start")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Summary")
    print_info("This example demonstrated:")
    print_info("  1. health_check() - Checks if the indexer service is healthy")
    print_info("")
    print_info("Health check response fields explained:")
    print_info("  - version: The version of the indexer software")
    print_info("  - db_available: Whether the database is accessible")
    print_info("  - is_migrating: Whether a database migration is in progress")
    print_info("  - message: A human-readable status message")
    print_info("  - round: The latest block round the indexer has processed")
    print_info("  - errors: Any error messages from the indexer")


if __name__ == "__main__":
    main()
