import warnings

from typing_extensions import deprecated

warnings.warn(
    """The legacy v2 application_specification module is deprecated and will be removed in a future version.
    Use `from algokit_utils.applications.app_spec.arc32 import ...` to access Arc32 app spec instead.
    By default, the ARC52Contract is a recommended app spec to use, serving as a replacement
    for legacy 'ApplicationSpecification' class.
    To convert legacy app specs to ARC52, use `Arc56Contract.from_arc32`.
""",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils.applications.app_spec.arc32 import (  # noqa: E402  # noqa: E402
    AppSpecStateDict,
    Arc32Contract,
    CallConfig,
    DefaultArgumentDict,
    DefaultArgumentType,
    MethodConfigDict,
    MethodHints,
    OnCompleteActionName,
)


@deprecated(
    "Use `Arc32Contract` from algokit_utils.applications instead. Example:\n"
    "```python\n"
    "from algokit_utils.applications import Arc32Contract\n"
    "app_spec = Arc32Contract.from_json(app_spec_json)\n"
    "```"
)
class ApplicationSpecification(Arc32Contract):
    """Deprecated class for ARC-0032 application specification"""


__all__ = [
    "AppSpecStateDict",
    "ApplicationSpecification",
    "CallConfig",
    "DefaultArgumentDict",
    "DefaultArgumentType",
    "MethodConfigDict",
    "MethodHints",
    "OnCompleteActionName",
]
