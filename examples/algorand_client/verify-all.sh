#!/bin/bash

# verify-all.sh - Run all algorand_client examples and verify they work
# Exit with non-zero code if any example fails

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN="$SCRIPT_DIR/../run.sh"
cd "$SCRIPT_DIR"

# Array of example files in order
EXAMPLES=(
    "01_client_instantiation.py"
    "02_algo_amount.py"
    "03_signer_config.py"
    "04_params_config.py"
    "05_account_manager.py"
    "06_send_payment.py"
    "07_send_asset_ops.py"
    "08_send_app_ops.py"
    "09_create_transaction.py"
    "10_transaction_composer.py"
    "11_asset_manager.py"
    "12_app_manager.py"
    "13_app_deployer.py"
    "14_client_manager.py"
    "15_error_transformers.py"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "========================================"
echo "Algorand Client Examples Verification Script"
echo "========================================"
echo ""

if [ ${#EXAMPLES[@]} -eq 0 ]; then
    echo "No examples to run yet."
    echo ""
    echo -e "${GREEN}Algorand Client examples suite passed (no examples)${NC}"
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
    if OUTPUT=$("$RUN" "$example" 2>&1); then
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
echo -e "${GREEN}All Algorand Client examples passed!${NC}"
exit 0
