#!/bin/bash

# verify-all.sh - Run all abi examples and verify they work
# Exit with non-zero code if any example fails

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Array of example files in order
# Add Python example files here as they are created
EXAMPLES=(
    "01_type_parsing.py"
    "02_primitive_types.py"
    "03_address_type.py"
    "04_string_type.py"
    "05_static_array.py"
    "06_dynamic_array.py"
    "07_tuple_type.py"
    "08_struct_type.py"
    "09_struct_tuple_conversion.py"
    "10_bool_packing.py"
    "11_abi_method.py"
    "12_avm_types.py"
    "13_type_guards.py"
    "14_complex_nested.py"
    "15_arc56_storage.py"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "========================================"
echo "ABI Examples Verification Script"
echo "========================================"
echo ""

if [ ${#EXAMPLES[@]} -eq 0 ]; then
    echo "No examples to run yet."
    echo ""
    echo -e "${GREEN}ABI examples suite passed (no examples)${NC}"
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
echo -e "${GREEN}All ABI examples passed!${NC}"
exit 0
