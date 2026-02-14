#!/usr/bin/env bash
# Generate API reference markdown from Python source using Sphinx + autoapi,
# then post-process the output for Starlight consumption.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_OUT="$SCRIPT_DIR/src/content/docs/api"

echo "==> Cleaning previous API output..."
rm -rf "$API_OUT"
mkdir -p "$API_OUT"

echo "==> Running Sphinx markdown build..."
cd "$REPO_ROOT"
uv run sphinx-build -b markdown docs/sphinx "$API_OUT" -q

echo "==> Removing Sphinx artifacts..."
rm -f "$API_OUT/.buildinfo"
rm -rf "$API_OUT/.doctrees"
# Remove the top-level index.md generated from index.rst (not needed in Starlight)
rm -f "$API_OUT/index.md"

echo "==> Injecting Starlight frontmatter into API docs..."
# Process each .md file: prepend YAML frontmatter with title derived from filename
find "$API_OUT" -name "*.md" -type f | while read -r file; do
    # Extract a human-readable title from the first H1 heading, or fall back to filename
    first_heading=$(grep -m1 '^# ' "$file" | sed 's/^# //' || true)
    if [ -z "$first_heading" ]; then
        # Derive title from filename: algokit_utils.md -> algokit_utils
        basename_no_ext=$(basename "$file" .md)
        first_heading="$basename_no_ext"
    fi

    # Escape double quotes in the title for YAML safety
    escaped_title=$(echo "$first_heading" | sed 's/"/\\"/g')

    # Create a temp file with frontmatter prepended
    tmp_file=$(mktemp)
    {
        echo "---"
        echo "title: \"$escaped_title\""
        echo "---"
        echo ""
        cat "$file"
    } > "$tmp_file"
    mv "$tmp_file" "$file"
done

echo "==> API docs generated at: $API_OUT"
echo "    $(find "$API_OUT" -name '*.md' | wc -l | tr -d ' ') markdown files"