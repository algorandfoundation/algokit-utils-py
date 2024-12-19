import warnings

warnings.warn(
    """The legacy v2 application_specification module is deprecated and will be removed in a future version.
    Use `from algokit_utils.applications.app_spec.arc32 import ...` to access Arc32 app spec instead.
    By default, the ARC52Contract is a recommended app spec to use, serving as a replacement
    for legacy 'ApplicationSpecification' class.
    To convert legacy app specs to ARC52, use `arc32_to_arc52` function from algokit_utils.applications.utils.
""",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils.applications.app_spec.arc32 import (  # noqa: E402
    AppSpecStateDict,
    CallConfig,
    DefaultArgumentDict,
    DefaultArgumentType,
    MethodConfigDict,
    MethodHints,
    OnCompleteActionName,
)
from algokit_utils.applications.app_spec.arc32 import (  # noqa: E402
    Arc32Contract as ApplicationSpecification,
)

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
