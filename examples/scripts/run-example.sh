#!/bin/bash
# Run a single example file using uv from the examples directory.
#
# Usage:
#   ./scripts/run-example.sh <file-or-path>
#
# Examples:
#   ./scripts/run-example.sh abi/01_type_parsing.py
#   ./scripts/run-example.sh transact/01_payment_transaction.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$1" ]; then
    echo "Usage: ./scripts/run-example.sh <file-or-path>"
    echo ""
    echo "Examples:"
    echo "  ./scripts/run-example.sh abi/01_type_parsing.py"
    echo "  ./scripts/run-example.sh transact/01_payment_transaction.py"
    exit 1
fi

INPUT="$1"
shift

# Try resolving the path relative to cwd, then relative to examples dir
if [ -f "$INPUT" ]; then
    RESOLVED="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"
elif [ -f "$EXAMPLES_DIR/$INPUT" ]; then
    RESOLVED="$EXAMPLES_DIR/$INPUT"
else
    # Search category subdirectories for a matching filename
    MATCHES=()
    for dir in "$EXAMPLES_DIR"/*/; do
        if [ -f "$dir$INPUT" ]; then
            MATCHES+=("$dir$INPUT")
        fi
    done

    if [ ${#MATCHES[@]} -eq 1 ]; then
        RESOLVED="${MATCHES[0]}"
    elif [ ${#MATCHES[@]} -gt 1 ]; then
        echo "Ambiguous example name \"$INPUT\". Matches:"
        for m in "${MATCHES[@]}"; do
            echo "  - $(realpath --relative-to="$EXAMPLES_DIR" "$m")"
        done
        exit 1
    else
        echo "Example not found: $INPUT"
        exit 1
    fi
fi

cd "$EXAMPLES_DIR"
exec uv run python "$RESOLVED" "$@"
