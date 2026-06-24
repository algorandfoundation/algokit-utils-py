# Isolated Sphinx configuration for API-only markdown generation.
# This config is used by docs/api_build.py to generate API reference
# markdown that is consumed by Starlight. It intentionally omits HTML
# themes, MyST, and other presentation-layer extensions.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx

from docutils import nodes

project = "algokit-utils-py"
copyright = "2026, Algorand Foundation"
author = "Algorand Foundation"
release = "3.0"

extensions = ["autoapi.extension"]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- AutoAPI configuration ---------------------------------------------------

autoapi_dirs = ["../../src/algokit_utils"]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]

autoapi_ignore = [
    "*algokit_utils/beta/__init__.py",
    "*algokit_utils/beta/account_manager.py",
    "*algokit_utils/beta/algorand_client.py",
    "*algokit_utils/beta/client_manager.py",
    "*algokit_utils/beta/composer.py",
    "*algokit_utils/asset.py",
    "*algokit_utils/deploy.py",
    "*algokit_utils/network_clients.py",
    "*algokit_utils/common.py",
    "*algokit_utils/account.py",
    "*algokit_utils/application_client.py",
    "*algokit_utils/application_specification.py",
    "*algokit_utils/logic_error.py",
    "*algokit_utils/dispenser_api.py",
]


# -- Pycon-to-Python conversion hook -----------------------------------------
# Starlight's Expressive Code doesn't support the "pycon" lexer.
# This hook converts pycon/doctest code blocks to plain Python and
# strips REPL prompts so syntax highlighting works correctly.


def _strip_pycon_prompts(text: str) -> str:
    """Return text with leading REPL prompts (>>>/...) stripped from each line."""
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith(">>> "):
            cleaned_lines.append(line[4:])
            continue
        if line.startswith(">>>"):
            cleaned_lines.append(line[3:].lstrip())
            continue
        if line.startswith("... "):
            cleaned_lines.append(line[4:])
            continue
        if line.startswith("..."):
            cleaned_lines.append(line[3:].lstrip())
            continue
        if line.startswith("\u2026 "):  # typographic ellipsis
            cleaned_lines.append(line[2:])
            continue
        if line.startswith("\u2026"):
            cleaned_lines.append(line[1:].lstrip())
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def convert_pycon_blocks_to_python(app, doctree, docname):
    """Convert pycon/doctest code blocks to python and strip prompts for Markdown."""
    if app.builder.name != "markdown":
        return

    for node in list(doctree.traverse(nodes.literal_block)):
        language = node.get("language")
        if language in {"pycon", "doctest"}:
            text = node.astext()
            node["language"] = "python"
            node.children = [nodes.Text(_strip_pycon_prompts(text))]

    doctest_block = getattr(nodes, "doctest_block", None)
    if doctest_block is not None:
        for node in list(doctree.traverse(doctest_block)):
            text = node.astext()
            code_text = _strip_pycon_prompts(text)
            replacement = nodes.literal_block(code_text, code_text)
            replacement["language"] = "python"
            node.replace_self(replacement)

    for field in doctree.traverse(nodes.field):
        if len(field) < 2 or not isinstance(field[0], nodes.field_name):
            continue
        field_name_text = field[0].astext().strip().lower()
        if field_name_text not in {"example", "examples"}:
            continue
        field_body = field[1]
        if not isinstance(field_body, nodes.field_body):
            continue
        for child in list(field_body.children):
            if not isinstance(child, (nodes.paragraph, nodes.block_quote)):
                continue
            text = child.astext()
            lines = text.splitlines()
            is_doctest = any(l.strip().startswith((">>>", "...", "\u2026")) for l in lines)
            if not is_doctest:
                continue
            code_text = _strip_pycon_prompts(text)
            replacement = nodes.literal_block(code_text, code_text)
            replacement["language"] = "python"
            child.replace_self(replacement)


def setup(app):
    """Sphinx extension setup function."""
    app.connect("doctree-resolved", convert_pycon_blocks_to_python)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
