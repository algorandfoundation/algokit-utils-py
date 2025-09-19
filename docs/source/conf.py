# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from __future__ import annotations

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

extensions = ['myst_parser', 'autoapi.extension', "sphinx.ext.autosectionlabel", "sphinx.ext.githubpages"]

templates_path = ['_templates']
exclude_patterns = []

autoapi_dirs = ['../../src/algokit_utils']
autoapi_options = ['members',
                   'undoc-members',
                   'show-inheritance',
                   # Removed 'show-module-summary' to reduce index.md files
                   ]
autoapi_own_page_level = 'class'  # Even flatter structure - consolidates more content per page
autoapi_add_toctree_entry = False  # Don't add to main TOC, we'll handle this manually

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

def setup(app):
    """Sphinx extension setup function."""
    app.connect('build-finished', copy_images_for_markdown)
    app.connect('doctree-resolved', fix_image_paths_in_doctree)
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
