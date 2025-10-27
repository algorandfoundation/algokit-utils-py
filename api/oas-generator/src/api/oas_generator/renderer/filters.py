from __future__ import annotations

import textwrap
from typing import Any


def docstring(text: str | None, indent: int = 4, width: int = 88) -> str:
    if not text:
        return ""
    indent_str = " " * indent
    body = textwrap.dedent(text).strip().splitlines()
    rendered_lines: list[str] = []
    for line in body:
        if not line:
            rendered_lines.append("")
            continue
        wrapped = textwrap.fill(line, width=width)
        rendered_lines.extend(wrapped.splitlines())
    rendered = "\n".join(f"{indent_str}{line}" if line else "" for line in rendered_lines)
    return f'{indent_str}"""\n{rendered}\n{indent_str}"""\n'


def descriptor_literal(descriptor: object, indent: int = 0) -> str:
    if descriptor is None:
        return "{}"
    fields: dict[str, Any] = {}
    for key in ("is_binary", "model", "list_model", "enum", "list_enum"):
        value = getattr(descriptor, key, None)
        if value is not None:
            fields[key] = value
    if not fields:
        return "{}"
    indent_str = " " * indent
    inner_indent = indent_str + " " * 4
    lines = [f'{inner_indent}"{key}": {value!r},' for key, value in fields.items()]
    body = "\n".join(lines)
    return f"{{\n{body}\n{indent_str}}}"


def optional_hint(type_hint: str) -> str:
    return type_hint if "| None" in type_hint else f"{type_hint} | None"


__all__ = ["descriptor_literal", "docstring", "optional_hint"]
