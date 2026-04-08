#!/bin/bash

# verify-all.sh - Run all indexer_client examples and verify they work
# Exit with non-zero code if any example fails

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Array of example files in order
EXAMPLES=(
    "01_health_check.py"
    "02_account_lookup.py"
    "03_account_assets.py"
    "04_account_applications.py"
    "05_account_transactions.py"
    "06_transaction_lookup.py"
    "07_transaction_search.py"
    "08_asset_lookup.py"
    "09_asset_balances.py"
    "10_asset_transactions.py"
    "11_application_lookup.py"
    "12_application_logs.py"
    "13_application_boxes.py"
    "14_block_lookup.py"
    "15_block_headers.py"
    "16_pagination.py"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "========================================"
echo "Indexer Client Examples Verification Script"
echo "========================================"
echo ""

if [ ${#EXAMPLES[@]} -eq 0 ]; then
    echo "No examples to run yet."
    echo ""
    echo -e "${GREEN}Indexer Client examples suite passed (no examples)${NC}"
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
echo -e "${GREEN}All Indexer Client examples passed!${NC}"
exit 0
