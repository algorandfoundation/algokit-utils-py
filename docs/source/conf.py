from sphinx.domains.python import PythonDomain

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "algokit-utils"
copyright = "2023, Algorand Foundation"
author = "Algorand Foundation"
release = "1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "autodoc2",
]
templates_path = ["_templates"]
exclude_patterns = []
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "algosdk": ("https://py-algorand-sdk.readthedocs.io/en/latest", None),
    "pyteal": ("https://pyteal.readthedocs.io/en/stable/", None),
}
# allows type aliases to be used as type references
PythonDomain.object_types["data"].roles = ("data", "class", "obj")


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# -- Options for myst ---
myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
]


# -- Options for autodoc2 ---
autodoc2_packages = [
    {
        "path": "../../src/algokit_utils",
        # "auto_mode": False,
    },
]
autodoc2_skip_module_regexes = [r"algokit_utils\..*"]
autodoc2_module_all_regexes = [
    r"algokit_utils",
]
autodoc2_docstring_parser_regexes = [
    # this will render all docstrings as Markdown
    (r".*", "myst"),
]
autodoc2_hidden_objects = [
    "undoc",  # undocumented objects
    "dunder",  # double-underscore methods, e.g. __str__
    "private",  # single-underscore methods, e.g. _private
    "inherited",
]
autodoc2_render_plugin = "myst"
autodoc2_sort_names = True
autodoc2_index_template = None
