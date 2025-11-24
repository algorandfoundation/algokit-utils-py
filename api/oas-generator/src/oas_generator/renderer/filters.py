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
    bool_fields = ("is_binary", "is_raw_msgpack")
    for key in bool_fields:
        if getattr(descriptor, key, False):
            fields[key] = True
    for key in ("model", "list_model", "enum", "list_enum"):
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


def response_decode_arguments(descriptor: object, indent: int = 0) -> str:
    if descriptor is None:
        return ""
    model = getattr(descriptor, "model", None) or getattr(descriptor, "enum", None)
    list_model = getattr(descriptor, "list_model", None) or getattr(descriptor, "list_enum", None)
    is_binary = bool(getattr(descriptor, "is_binary", False))
    raw_msgpack = bool(getattr(descriptor, "is_raw_msgpack", False))
    type_hint = getattr(descriptor, "type_hint", None)
    parts: list[str] = []
    if is_binary:
        parts.append("is_binary=True")
    if raw_msgpack:
        parts.append("raw_msgpack=True")
    if model:
        parts.append(f"model=models.{model}")
    if list_model:
        parts.append(f"list_model=models.{list_model}")
    if not model and not list_model and not is_binary and not raw_msgpack and type_hint and type_hint != "object":
        parts.append(f"type_={type_hint}")
    if not parts:
        return ""
    indent_str = " " * indent
    separator = ",\n" + indent_str
    return ",\n" + indent_str + separator.join(parts)


def optional_hint(type_hint: str) -> str:
    return type_hint if "| None" in type_hint else f"{type_hint} | None"


__all__ = ["descriptor_literal", "docstring", "optional_hint", "response_decode_arguments"]
