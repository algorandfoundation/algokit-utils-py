import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Environment variable to override the project root
ALGOKIT_PROJECT_ROOT = os.getenv("ALGOKIT_PROJECT_ROOT")
ALGOKIT_CONFIG_FILENAME = ".algokit.toml"


class AlgoKitLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("algokit")
        self._setup_logger()

    def _setup_logger(self) -> None:
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def _get_logger(self, *, suppress_log: bool = False) -> logging.Logger:
        if suppress_log:
            null_logger = logging.getLogger("null")
            null_logger.addHandler(logging.NullHandler())
            return null_logger
        return self._logger

    def error(self, message: str, *args: Any, suppress_log: bool = False, **kwargs: Any) -> None:
        """Log an error message, optionally suppressing output"""
        self._get_logger(suppress_log=suppress_log).error(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, suppress_log: bool = False, **kwargs: Any) -> None:
        """Log an exception message, optionally suppressing output"""
        self._get_logger(suppress_log=suppress_log).exception(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, suppress_log: bool = False, **kwargs: Any) -> None:
        """Log a warning message, optionally suppressing output"""
        self._get_logger(suppress_log=suppress_log).warning(message, *args, **kwargs)

    def info(self, message: str, *args: Any, suppress_log: bool = False, **kwargs: Any) -> None:
        """Log an info message, optionally suppressing output"""
        self._get_logger(suppress_log=suppress_log).info(message, *args, **kwargs)

    def debug(self, message: str, *args: Any, suppress_log: bool = False, **kwargs: Any) -> None:
        """Log a debug message, optionally suppressing output"""
        self._get_logger(suppress_log=suppress_log).debug(message, *args, **kwargs)

    def verbose(self, message: str, *args: Any, suppress_log: bool = False, **kwargs: Any) -> None:
        """Log a verbose message (maps to debug), optionally suppressing output"""
        self._get_logger(suppress_log=suppress_log).debug(message, *args, **kwargs)


class UpdatableConfig:
    """Class to manage and update configuration settings for the AlgoKit project.

    Attributes:
        debug (bool): Indicates whether debug mode is enabled.
        project_root (Path | None): The path to the project root directory.
        trace_all (bool): Indicates whether to trace all operations.
        trace_buffer_size_mb (int): The size of the trace buffer in megabytes.
        max_search_depth (int): The maximum depth to search for a specific file.
        populate_app_call_resources (bool): Indicates whether to populate app call resources.
    """

    def __init__(self) -> None:
        self._logger = AlgoKitLogger()
        self._debug: bool = False
        self._project_root: Path | None = None
        self._trace_all: bool = False
        self._trace_buffer_size_mb: int | float = 256  # megabytes
        self._max_search_depth: int = 10
        self._populate_app_call_resources: bool = False
        self._configure_project_root()

    def _configure_project_root(self) -> None:
        """Configures the project root by searching for a specific file within a depth limit."""
        current_path = Path(__file__).resolve()
        for _ in range(self._max_search_depth):
            self.logger.debug(f"Searching in: {current_path}")
            if (current_path / ALGOKIT_CONFIG_FILENAME).exists():
                self._project_root = current_path
                break
            current_path = current_path.parent

    @property
    def logger(self) -> AlgoKitLogger:
        return self._logger

    @property
    def debug(self) -> bool:
        """Returns the debug status."""
        return self._debug

    @property
    def project_root(self) -> Path | None:
        """Returns the project root path."""
        return self._project_root

    @property
    def trace_all(self) -> bool:
        """Indicates whether to store simulation traces for all operations."""
        return self._trace_all

    @property
    def trace_buffer_size_mb(self) -> int | float:
        """Returns the size of the trace buffer in megabytes."""
        return self._trace_buffer_size_mb

    @property
    def populate_app_call_resource(self) -> bool:
        return self._populate_app_call_resources

    def with_debug(self, func: Callable[[], str | None]) -> None:
        """Executes a function with debug mode temporarily enabled."""
        original_debug = self._debug
        try:
            self._debug = True
            func()
        finally:
            self._debug = original_debug

    def configure(
        self,
        *,
        debug: bool | None = None,
        project_root: Path | None = None,
        trace_all: bool = False,
        trace_buffer_size_mb: float = 256,
        max_search_depth: int = 10,
        populate_app_call_resources: bool = False,
    ) -> None:
        """
        Configures various settings for the application.
        Please note, when `project_root` is not specified, by default config will attempt to find the `algokit.toml` by
        scanning the parent directories according to the `max_search_depth` parameter.
        Alternatively value can also be set via the `ALGOKIT_PROJECT_ROOT` environment variable.
        If you are executing the config from an algokit compliant project, you can simply call
        `config.configure(debug=True)`.

        :param debug: Indicates whether debug mode is enabled.
        :param project_root: The path to the project root directory. Defaults to None.
        :param trace_all: Indicates whether to trace all operations. Defaults to False. Which implies that
                only the operations that are failed will be traced by default.
        :param trace_buffer_size_mb: The size of the trace buffer in megabytes. Defaults to 256
        :param max_search_depth: The maximum depth to search for a specific file. Defaults to 10
        :param populate_app_call_resources: Indicates whether to populate app call resources. Defaults to False
        """

        if debug is not None:
            self._debug = debug
        if project_root is not None:
            self._project_root = project_root.resolve(strict=True)
        elif debug is not None and ALGOKIT_PROJECT_ROOT:
            self._project_root = Path(ALGOKIT_PROJECT_ROOT).resolve(strict=True)

        self._trace_all = trace_all
        self._trace_buffer_size_mb = trace_buffer_size_mb
        self._max_search_depth = max_search_depth
        self._populate_app_call_resources = populate_app_call_resources


config = UpdatableConfig()
