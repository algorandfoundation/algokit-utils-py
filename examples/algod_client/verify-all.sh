#!/bin/bash

# verify-all.sh - Run all algod_client examples and verify they work
# Exit with non-zero code if any example fails

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Array of example files in order
EXAMPLES=(
    "01_node_health_status.py"
    "02_version_genesis.py"
    "03_ledger_supply.py"
    "04_account_info.py"
    "05_transaction_params.py"
    "06_send_transaction.py"
    "07_pending_transactions.py"
    "08_block_data.py"
    "09_asset_info.py"
    "10_application_info.py"
    "11_application_boxes.py"
    "12_teal_compile.py"
    "13_simulation.py"
    "14_state_deltas.py"
    "15_transaction_proof.py"
    "16_lightblock_proof.py"
    "17_state_proof.py"
    "18_devmode_timestamp.py"
    "19_sync_round.py"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "========================================"
echo "Algod Client Examples Verification Script"
echo "========================================"
echo ""

if [ ${#EXAMPLES[@]} -eq 0 ]; then
    echo "No examples to run yet."
    echo ""
    echo -e "${GREEN}Algod Client examples suite passed (no examples)${NC}"
    exit 0
fi

PASSED=0
FAILED=0
FAILED_EXAMPLES=()

for example in "${EXAMPLES[@]}"; do
    echo -n "Running $example... "

    if [ ! -f "$example" ]; then
        echo -e "${RED}FAILED${NC} (file not found)"
        FAILED=$((FAILED + 1))
        FAILED_EXAMPLES+=("$example")
        continue
    fi

    # Run the example and capture output/exit code
    if OUTPUT=$(uv run python "$example" 2>&1); then
        echo -e "${GREEN}PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}FAILED${NC}"
        echo "$OUTPUT"
        FAILED=$((FAILED + 1))
        FAILED_EXAMPLES+=("$example")
    fi
done

echo ""
echo "========================================"
echo "Results: ${PASSED} passed, ${FAILED} failed"
echo "========================================"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed examples:${NC}"
    for failed in "${FAILED_EXAMPLES[@]}"; do
        echo "  - $failed"
    done
    exit 1
fi

echo ""
echo -e "${GREEN}All Algod Client examples passed!${NC}"
exit 0
