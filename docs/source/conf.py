# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.domains.python import PyObject

project = 'algokit-utils-py'
copyright = '2025, Algorand Foundation'
author = 'Algorand Foundation'
release = '3.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser', 'autoapi.extension', "sphinx.ext.autosectionlabel"]

templates_path = ['_templates']
exclude_patterns = []

autoapi_dirs = ['../../src/algokit_utils']
autoapi_options = ['members', 
                   'undoc-members',  
                   'show-inheritance', 
                   'show-module-summary', 
                   ]

autoapi_ignore = ['*algokit_utils/beta/__init__.py', 
                  '*algokit_utils/beta/account_manager.py', 
                  '*algokit_utils/beta/algorand_client.py', 
                  '*algokit_utils/beta/client_manager.py', 
                  '*algokit_utils/beta/composer.py', 
                  '*algokit_utils/asset.py', 
                  '*algokit_utils/deploy.py', 
                  "*algokit_utils/network_clients.py", 
                  "*algokit_utils/common.py", 
                  "*algokit_utils/account.py", 
                  "*algokit_utils/application_client.py", 
                  "*algokit_utils/application_specification.py", 
                  "*algokit_utils/logic_error.py", 
                  "*algokit_utils/dispenser_api.py"]

myst_heading_anchors = 5
myst_all_links_external = False
autosectionlabel_prefix_document = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
pygments_style = "sphinx"
pygments_dark_style = "monokai"
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Copy images for markdown build
import os
import shutil
from pathlib import Path
from docutils import nodes

def copy_images_for_markdown(app, exception):
    """Copy images from source/images to markdown/images for markdown builds."""
    if app.builder.name == 'markdown':
        source_images = Path(app.srcdir) / 'images'
        dest_images = Path(app.outdir) / 'images'
        
        if source_images.exists():
            # Ensure destination directory exists
            dest_images.mkdir(parents=True, exist_ok=True)
            
            # Copy all image files
            for image_file in source_images.iterdir():
                if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
                    shutil.copy2(image_file, dest_images / image_file.name)
                    print(f"Copied {image_file.name} to {dest_images}")

def fix_image_paths_in_doctree(app, doctree, docname):
    """Fix image paths in doctree to preserve relative paths for markdown output."""
    if app.builder.name == 'markdown':
        for node in doctree.traverse(nodes.image):
            if 'uri' in node:
                uri = node['uri']
                # If the URI was resolved from ../images/ to images/, change it back
                if uri.startswith('images/') and not uri.startswith('../'):
                    node['uri'] = '../' + uri
                    print(f"Fixed image path: {uri} -> {node['uri']}")

def _strip_pycon_prompts(text: str) -> str:
    """Return text with leading REPL prompts (>>>/...) stripped from each line.

    This converts doctest-style examples into plain Python code for builders that
    don't support the "pycon" lexer.
    """
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        # Normalize common doctest continuation variants (ASCII '...' and typographic '…')
        if line.startswith('>>> '):
            cleaned_lines.append(line[4:])
            continue
        if line.startswith('>>>'):
            cleaned_lines.append(line[3:].lstrip())
            continue
        if line.startswith('... '):
            cleaned_lines.append(line[4:])
            continue
        if line.startswith('...'):
            cleaned_lines.append(line[3:].lstrip())
            continue
        if line.startswith('… '):  # typographic ellipsis
            cleaned_lines.append(line[2:])
            continue
        if line.startswith('…'):
            cleaned_lines.append(line[1:].lstrip())
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def convert_pycon_blocks_to_python(app, doctree, docname):
    """Convert pycon/doctest code blocks to python and strip prompts for Markdown.

    Some downstream renderers (e.g. Starlight's Expressive Code) don't support
    the "pycon" language. This hook normalizes such blocks to "python" and
    removes REPL prompts so syntax highlighting works and warnings are avoided.
    """
    if app.builder.name != 'markdown':
        return

    # Handle literal code blocks tagged as pycon/doctest
    for node in list(doctree.traverse(nodes.literal_block)):
        language = node.get('language')
        if language in {'pycon', 'doctest'}:
            text = node.astext()
            node['language'] = 'python'
            node.children = [nodes.Text(_strip_pycon_prompts(text))]

    # Handle explicit doctest block nodes if present
    doctest_block = getattr(nodes, 'doctest_block', None)
    if doctest_block is not None:
        for node in list(doctree.traverse(doctest_block)):
            text = node.astext()
            code_text = _strip_pycon_prompts(text)
            replacement = nodes.literal_block(code_text, code_text)
            replacement['language'] = 'python'
            node.replace_self(replacement)

    # Normalize doctest-style paragraphs and block quotes within Example fields
    for field in doctree.traverse(nodes.field):
        # Expect children: field_name, field_body
        if len(field) < 2 or not isinstance(field[0], nodes.field_name):
            continue
        field_name_text = field[0].astext().strip().lower()
        if field_name_text not in {'example', 'examples'}:
            continue
        field_body = field[1]
        if not isinstance(field_body, nodes.field_body):
            continue
        for child in list(field_body.children):
            if not isinstance(child, (nodes.paragraph, nodes.block_quote)):
                continue
            text = child.astext()
            # Heuristic: treat as doctest if any line starts with '>>>', '...'(ascii) or '…'(typographic)
            lines = text.splitlines()
            is_doctest = any(l.strip().startswith(('>>>', '...', '…')) for l in lines)
            if not is_doctest:
                continue
            code_text = _strip_pycon_prompts(text)
            replacement = nodes.literal_block(code_text, code_text)
            replacement['language'] = 'python'
            child.replace_self(replacement)

def setup(app):
    """Sphinx extension setup function."""
    app.connect('build-finished', copy_images_for_markdown)
    app.connect('doctree-resolved', fix_image_paths_in_doctree)
    app.connect('doctree-resolved', convert_pycon_blocks_to_python)
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
