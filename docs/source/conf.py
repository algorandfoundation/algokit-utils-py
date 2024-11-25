from __future__ import annotations

import typing as t

import typing_extensions as te
from autodoc2.render.myst_ import MystRenderer
from autodoc2.utils import ItemData
from sphinx.domains.python import PythonDomain


class AlgoKitRenderer(MystRenderer):
    """Render the documentation as MyST.

    Based on the code in
    https://github.com/bytewax/bytewax/blob/58bc1d9517f11578c914407a057960b76d8d9b1b/docs/renderer.py#L16

    """


    @te.override
    def render_class(self, item: ItemData) -> t.Iterable[str]:
        """Create the content for a class."""
        short_name = item["full_name"].split(".")[-1]
        constructor = self.get_item(f"{item['full_name']}.__init__")
        sig = short_name
        if constructor and "args" in constructor:
            args = self.format_args(
                constructor["args"], self.show_annotations(item), ignore_self="self"
            )
            sig += f"({args})"

        # note, here we can cannot yield by line,
        # because we need to look ahead to know the length of the backticks

        lines: list[str] = [f":canonical: {item['full_name']}"]
        if self.no_index(item):
            lines += [":noindex:"]
        lines += [""]

        # TODO overloads

        if item.get("bases") and self.show_class_inheritance(item):
            lines += [
                "Bases: "
                + ", ".join(
                    [self._reformat_cls_base_myst(b) for b in item.get("bases", [])]
                ),
                "",
            ]

        if self.show_docstring(item):
            lines.append(f"```{{autodoc2-docstring}} {item['full_name']}")
            if parser_name := self.get_doc_parser(item["full_name"]):
                lines.append(f":parser: {parser_name}")
            lines.append("```")
            lines.append("")

            if self.config.class_docstring == "merge":
                init_item = self.get_item(f"{item['full_name']}.__init__")
                if init_item:
                    lines.extend(
                        [
                            "Initialization",
                            "",
                            f"```{{autodoc2-docstring}} {init_item['full_name']}",
                        ]
                    )
                    if parser_name := self.get_doc_parser(init_item["full_name"]):
                        lines.append(f":parser: {parser_name}")
                    lines.extend(["```", ""])

        for child in self.get_children(
            item, {"class", "property", "attribute", "method"}
        ):
            if (
                child["full_name"].endswith(".__init__")
                and self.config.class_docstring == "merge"
            ):
                continue
            for line in self.render_item(child["full_name"]):
                lines.append(line)

        backticks = self.enclosing_backticks("\n".join(lines))
        yield f"{backticks}{{py:{item['type']}}} {sig}"
        for line in lines:
            yield line
        yield backticks
        yield ""

    @te.override
    def render_package(self, item: ItemData) -> t.Iterable[str]:  # noqa: C901
        if self.standalone and self.is_hidden(item):
            yield from ["---", "orphan: true", "---", ""]

        full_name = item["full_name"]

        yield f"# {{py:mod}}`{full_name}`"
        yield ""

        yield f"```{{py:module}} {full_name}"
        if self.no_index(item):
            yield ":noindex:"
        if self.is_module_deprecated(item):
            yield ":deprecated:"
        yield from ["```", ""]

        if self.show_docstring(item):
            yield f"```{{autodoc2-docstring}} {item['full_name']}"
            if parser_name := self.get_doc_parser(item["full_name"]):
                yield f":parser: {parser_name}"
            yield ":allowtitles:"
            yield "```"
            yield ""

        visible_submodules = [i["full_name"] for i in self.get_children(item, {"module", "package"})]
        if visible_submodules:
            yield "## Submodules"
            yield ""
            yield "```{toctree}"
            yield ":titlesonly:"
            yield ""
            yield from sorted(visible_submodules)
            yield "```"
            yield ""

        visible_children = [i["full_name"] for i in self.get_children(item) if i["type"] not in ("package", "module")]
        if not visible_children:
            return

        for heading, types in [
            ("Data", {"data"}),
            ("Classes", {"class"}),
            ("Functions", {"function"}),
            ("External", {"external"}),
        ]:
            visible_items = list(self.get_children(item, types))
            if visible_items:
                yield from [f"## {heading}", ""]
                for i in visible_items:
                    yield from self.render_item(i["full_name"])
                    yield ""


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "algokit-utils"
copyright = "2023, Algorand Foundation"  # noqa: A001
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
exclude_patterns = []  # type: ignore
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
html_static_path = []  # type: ignore


# -- Options for myst ---
myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
    "deflist",
    "tasklist",
    "attrs_inline",
    "attrs_block",
    "substitution",
    "linkify",
]

myst_heading_anchors = 3
myst_all_links_external = False

# -- Options for autodoc2 ---
autodoc2_packages = [
    {
        "path": "../../src/algokit_utils",
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
autodoc2_render_plugin = AlgoKitRenderer
autodoc2_sort_names = True
autodoc2_index_template = None
