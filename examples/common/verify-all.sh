#!/bin/bash

# verify-all.sh - Run all common examples and verify they work
# Exit with non-zero code if any example fails

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Array of example files in order
EXAMPLES=(
    "01_address_basics.py"
    "02_address_encoding.py"
    "03_array_utilities.py"
    "04_constants.py"
    "05_crypto_hash.py"
    "06_logger.py"
    "07_json_bigint.py"
    "08_msgpack.py"
    "09_primitive_codecs.py"
    "10_composite_codecs.py"
    "11_model_codecs.py"
    "12_sourcemap.py"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "========================================"
echo "Common Examples Verification Script"
echo "========================================"
echo ""

if [ ${#EXAMPLES[@]} -eq 0 ]; then
    echo "No examples to run yet."
    echo ""
    echo -e "${GREEN}Common examples suite passed (no examples)${NC}"
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
echo -e "${GREEN}All Common examples passed!${NC}"
exit 0
