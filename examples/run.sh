#!/bin/bash

# Helper to run individual examples with correct PYTHONPATH
# Usage: ./run.sh transact/01_payment_transaction.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHONPATH="$REPO_ROOT:$PYTHONPATH" uv run python "$@"
