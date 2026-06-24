#!/usr/bin/env python3
"""Generate API reference markdown from Python source using Sphinx + autoapi,
then post-process the output for Starlight consumption.

Replaces the former docs/api-build.sh with a cross-platform Python implementation
that includes better error handling and robustness.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_DIR.parent
API_OUT = DOCS_DIR / "src" / "content" / "docs" / "api"

# Regex patterns for shortening qualified names in headings
_HEADING_RE = re.compile(r"^#{3,4}\s")
_LINKED_QUALIFIED_RE = re.compile(
    r"\[(?:algokit_\w+|typing_extensions|collections\.abc|algokit_common)"
    r"(?:\.\w+)*\.(\w+)\]"
)
_PLAIN_QUALIFIED_RE = re.compile(
    r"(?<!\[)(?<!#)(?<!/)(?<!\.md)(?:algokit_\w+|typing_extensions|collections\.abc|algokit_common)"
    r"(?:\.\w+)*\.(\w+)"
)
_INDEX_MD_RE = re.compile(r"/index\.md")

# Matches *class* headings with constructor signatures: "### *class* Foo(\*args, \*\*kwds)"
_CLASS_ARGS_RE = re.compile(
    r"^(#{3,4} \*class\* \w+)\(.*\)\s*$",
    re.MULTILINE,
)
# Extracts H3 heading text for anchor map building
_H3_TEXT_RE = re.compile(r"^### (.+)$", re.MULTILINE)
# Matches qualified Sphinx anchors inside markdown link URLs
_QUALIFIED_ANCHOR_RE = re.compile(
    r"\(([^()\s\"']*?)#(?:algokit_\w+|typing_extensions|collections\.abc|algokit_common)"
    r"(?:\.\w+)*\.(\w+)\)"
)


def _clean_api_output() -> None:
    """Remove previous API output and create a fresh directory."""
    print("==> Cleaning previous API output...")
    if API_OUT.exists():
        shutil.rmtree(API_OUT)
    API_OUT.mkdir(parents=True, exist_ok=True)


def _run_sphinx_build() -> None:
    """Run Sphinx markdown build to generate API docs."""
    print("==> Running Sphinx markdown build...")
    result = subprocess.run(
        ["uv", "run", "sphinx-build", "-b", "markdown", "docs/sphinx", str(API_OUT), "-q"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"ERROR: Sphinx build failed (exit code {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        sys.exit(1)


def _remove_sphinx_artifacts() -> None:
    """Remove Sphinx build artifacts not needed by Starlight."""
    print("==> Removing Sphinx artifacts...")
    buildinfo = API_OUT / ".buildinfo"
    if buildinfo.exists():
        buildinfo.unlink()

    doctrees = API_OUT / ".doctrees"
    if doctrees.exists():
        shutil.rmtree(doctrees)

    # Remove top-level index.md generated from index.rst (not needed in Starlight)
    index_md = API_OUT / "index.md"
    if index_md.exists():
        index_md.unlink()


def _flatten_autoapi() -> None:
    """Flatten autoapi/ -- move algokit_utils/ up one level so Starlight sees api/algokit_utils/."""
    print("==> Flattening autoapi directory structure...")
    autoapi_algokit = API_OUT / "autoapi" / "algokit_utils"
    target = API_OUT / "algokit_utils"

    if not autoapi_algokit.is_dir():
        print(
            f"ERROR: Expected autoapi output directory not found: {autoapi_algokit}\n"
            "This likely means the Sphinx autoapi configuration or package structure has changed.\n"
            "Check that 'autoapi_dirs' in docs/sphinx/conf.py points to the correct source directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    if target.exists():
        shutil.rmtree(target)

    shutil.move(str(autoapi_algokit), str(target))

    # Clean up remaining autoapi directory
    autoapi_dir = API_OUT / "autoapi"
    if autoapi_dir.exists():
        shutil.rmtree(autoapi_dir)


def _extract_title(file_path: Path) -> str:
    """Extract a human-readable title from the first H1 heading, or fall back to filename."""
    with file_path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    return file_path.stem


def _inject_frontmatter() -> None:
    """Prepend YAML frontmatter with title to each API markdown file."""
    print("==> Injecting Starlight frontmatter into API docs...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        title = _extract_title(md_file)
        # Escape double quotes in the title for YAML safety
        escaped_title = title.replace('"', '\\"')

        content = md_file.read_text(encoding="utf-8")
        # Strip the H1 — Starlight renders title from frontmatter.
        content = re.sub(r"^# [^\n]*\n+", "", content)
        md_file.write_text(
            f'---\ntitle: "{escaped_title}"\n---\n\n<div class="api-ref">\n\n{content}\n\n</div>\n',
            encoding="utf-8",
        )


def _fix_internal_links() -> None:
    """Fix internal links for Starlight.

    Sphinx generates links like (foo/index.md) and (../../bar/index.md#anchor).
    Starlight doesn't use .md extensions -- strip index.md from link paths.
    """
    print("==> Fixing internal links for Starlight...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _INDEX_MD_RE.sub("/", content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def _shorten_qualified_names() -> None:
    """Shorten fully-qualified module paths in H3/H4 headings.

    Strip fully-qualified module paths from heading text so the TOC sidebar and
    headings show short names (e.g. "AccountManager" not "algokit_utils.x.y.AccountManager").
    Handles: algokit_utils.*, algokit_transact.*, algokit_common.*, typing_extensions.*, collections.abc.*
    Only applies to H3/H4 heading lines. Preserves full paths inside link URLs (...).
    """
    print("==> Shortening qualified names in headings...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        lines = md_file.read_text(encoding="utf-8").splitlines(keepends=True)
        changed = False
        for i, line in enumerate(lines):
            if not _HEADING_RE.match(line):
                continue
            new_line = _LINKED_QUALIFIED_RE.sub(r"[\1]", line)
            new_line = _PLAIN_QUALIFIED_RE.sub(r"\1", new_line)
            if new_line != line:
                lines[i] = new_line
                changed = True
        if changed:
            md_file.write_text("".join(lines), encoding="utf-8")


def _compute_starlight_anchor(heading_text: str) -> str:
    """Compute the anchor slug that Astro (github-slugger) generates from heading text.

    Mirrors github-slugger over the *rendered* text: markdown links/emphasis/code
    markers are stripped first, then punctuation is removed (underscores and
    hyphens are kept) and each space becomes a hyphen.
    """
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading_text)  # [text](url) → text
    text = re.sub(r"\\(.)", r"\1", text)  # \* → *
    text = text.replace("*", "").replace("`", "")  # em/code markers
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _simplify_class_headings() -> None:
    """Strip constructor signatures from *class* headings for predictable anchors.

    Converts: ### *class* Foo(\\*args, \\*\\*kwds)
    To:        ### *class* Foo

    Without this, Starlight generates messy anchors like #class-foo-args--kwds
    that don't match the plain #class-foo used in summary table links.
    """
    print("==> Simplifying class heading signatures...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _CLASS_ARGS_RE.sub(r"\1", content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def _fix_qualified_anchors() -> None:
    """Rewrite Sphinx-style qualified anchors to match Starlight heading IDs.

    Sphinx generates links like [Foo](#algokit_utils.module.Foo) but Starlight
    generates anchors from rendered heading text (e.g. #class-foo for
    '### *class* Foo').
    """
    print("==> Fixing qualified name anchors...")
    file_maps: dict[str, dict[str, str]] = {}
    for md_file in sorted(API_OUT.rglob("*.md")):
        anchor_map: dict[str, str] = {}
        content = md_file.read_text(encoding="utf-8")
        for m in _H3_TEXT_RE.finditer(content):
            heading_text = m.group(1)
            key_m = re.match(r"(?:\*\w+\*\s+)?(\w+)", heading_text)
            if key_m:
                symbol = key_m.group(1)
                anchor_map[symbol] = _compute_starlight_anchor(heading_text)
        file_maps[str(md_file)] = anchor_map

    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")

        def fix_anchor(m: re.Match, _file: Path = md_file) -> str:
            path_part, symbol = m.group(1), m.group(2)
            if path_part:
                target_md = (_file.parent / path_part).resolve() / "index.md"
            else:
                target_md = _file
            anchor = file_maps.get(str(target_md), {}).get(symbol, symbol.lower())
            return f"({path_part}#{anchor})"

        updated = _QUALIFIED_ANCHOR_RE.sub(fix_anchor, content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


_HEADING_LINE_RE = re.compile(r"^#{2,6}\s+(.+?)\s*$", re.MULTILINE)
_ANCHOR_LINK_RE = re.compile(r"\]\(([^()\s#`\"']*)#([A-Za-z0-9_.\-]+)\)")
_NESTED_URL_LINK_RE = re.compile(r"\]\(\[(https?://[^\]\s]+)\]\(\1\)\)")


def _norm_slug(slug: str) -> str:
    """Normalise a slug for cross-slugger comparison (sphinx-markdown-builder vs github-slugger)."""
    return re.sub(r"-+", "-", slug.replace("_", "-")).strip("-")


def _fix_signature_anchors() -> None:
    """Repair links whose anchors were slugged by sphinx-markdown-builder, not github-slugger.

    Function/data headings keep their full signatures, so Sphinx's summary-table links
    (e.g. #get-abi-decoded-value-value-bytes-...) don't match the IDs Astro generates
    (e.g. #get_abi_decoded_value-value-bytes--int--str-...). For every anchor link that
    doesn't match a real heading ID, find the heading it refers to (exact normalised
    match, else longest signature-less prefix match) and rewrite the slug.
    """
    print("==> Repairing signature heading anchors...")
    anchors: dict[Path, set[str]] = {}
    norm_full: dict[Path, dict[str, str]] = {}
    norm_prefix: dict[Path, list[tuple[str, str]]] = {}

    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        seen: dict[str, int] = {}
        anchors[md_file] = set()
        norm_full[md_file] = {}
        norm_prefix[md_file] = []
        for m in _HEADING_LINE_RE.finditer(content):
            text = m.group(1)
            slug = _compute_starlight_anchor(text)
            # github-slugger dedupes repeated headings with -1, -2, ... suffixes
            if slug in seen:
                seen[slug] += 1
                actual = f"{slug}-{seen[slug]}"
            else:
                seen[slug] = 0
                actual = slug
            anchors[md_file].add(actual)
            norm_full[md_file].setdefault(_norm_slug(actual), actual)
            prefix = _compute_starlight_anchor(text.split("(")[0]) if "(" in text else slug
            norm_prefix[md_file].append((_norm_slug(prefix), actual))

    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")

        def fix(m: re.Match, _file: Path = md_file) -> str:
            path_part, slug = m.group(1), m.group(2)
            if path_part:
                if path_part.startswith(("http://", "https://")):
                    return m.group(0)
                target = (_file.parent / path_part).resolve()
                target = target if target.suffix == ".md" else target / "index.md"
            else:
                target = _file
            if target not in anchors or slug in anchors[target]:
                return m.group(0)
            n = _norm_slug(slug)
            if n in norm_full[target]:
                return f"]({path_part}#{norm_full[target][n]})"
            best = None
            for prefix, actual in norm_prefix[target]:
                if (n == prefix or n.startswith(prefix + "-")) and (best is None or len(prefix) > best[0]):
                    best = (len(prefix), actual)
            if best:
                return f"]({path_part}#{best[1]})"
            return m.group(0)

        updated = _ANCHOR_LINK_RE.sub(fix, content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def _fix_nested_url_links() -> None:
    """Unwrap [text]([url](url)) links produced when Sphinx auto-linkifies URLs in docstrings."""
    print("==> Unwrapping auto-linkified URLs...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _NESTED_URL_LINK_RE.sub(r"](\1)", content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def main() -> None:
    """Run the full API docs build pipeline."""
    _clean_api_output()
    _run_sphinx_build()
    _remove_sphinx_artifacts()
    _flatten_autoapi()
    _inject_frontmatter()
    _fix_internal_links()
    _shorten_qualified_names()
    _simplify_class_headings()
    _fix_qualified_anchors()
    _fix_signature_anchors()
    _fix_nested_url_links()

    file_count = sum(1 for _ in API_OUT.rglob("*.md"))
    print(f"==> API docs generated at: {API_OUT}")
    print(f"    {file_count} markdown files")


if __name__ == "__main__":
    main()
