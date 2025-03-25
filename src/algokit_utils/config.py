import logging
import os
from collections.abc import Callable
from pathlib import Path

# Environment variable to override the project root
ALGOKIT_PROJECT_ROOT = os.getenv("ALGOKIT_PROJECT_ROOT")
ALGOKIT_CONFIG_FILENAME = ".algokit.toml"


class AlgoKitLogger(logging.Logger):
    def __init__(self, name: str = "algokit-utils-py", level: int = logging.NOTSET):
        super().__init__(name, level)

    def _log(self, level: int, msg: object, args, exc_info=None, extra=None, stack_info=False, stacklevel=1) -> None:  # type: ignore[no-untyped-def]  # noqa: FBT002, ANN001
        """
        Overrides the base _log method to allow suppressing individual log calls.
        When a caller passes suppress_log=True in the extra keyword, the log call is ignored.
        """

        # Check if the 'suppress_log' flag is provided in the extra dictionary.
        if extra and extra.get("suppress_log", False):
            return
        # Call the parent _log
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

    @classmethod
    def get_null_logger(cls) -> logging.Logger:
        """Return a logger that does nothing (a null logger)."""
        null_logger = logging.getLogger("null")
        null_logger.handlers.clear()
        null_logger.addHandler(logging.NullHandler())
        null_logger.propagate = False
        return null_logger


# Set our custom logger class as the default.
logging.setLoggerClass(AlgoKitLogger)


class UpdatableConfig:
    """
    Class to manage and update configuration settings for the AlgoKit project.

    Attributes:
        debug (bool): Indicates whether debug mode is enabled.
        project_root (Path | None): The path to the project root directory.
        trace_all (bool): Indicates whether to trace all operations.
        trace_buffer_size_mb (int | float): The size of the trace buffer in megabytes.
        max_search_depth (int): The maximum depth to search for a specific file.
        populate_app_call_resources (bool): Whether to populate app call resources.
        logger (logging.Logger): The logger instance to use. Defaults to an AlgoKitLogger instance.
    """

    def __init__(self) -> None:
        self._logger: logging.Logger = AlgoKitLogger()
        self._debug: bool = False
        self._project_root: Path | None = None
        self._trace_all: bool = False
        self._trace_buffer_size_mb: int | float = 256  # megabytes
        self._max_search_depth: int = 10
        self._populate_app_call_resources: bool = True
        self._configure_project_root()

    def _configure_project_root(self) -> None:
        """
        Configures the project root by searching for a specific file within a depth limit.
        """
        current_path = Path(__file__).resolve()
        for _ in range(self._max_search_depth):
            self._logger.debug(f"Searching in: {current_path}")
            if (current_path / ALGOKIT_CONFIG_FILENAME).exists():
                self._project_root = current_path
                break
            current_path = current_path.parent

    @property
    def logger(self) -> logging.Logger:
        """Returns the logger instance."""
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
        """Indicates whether simulation traces for all operations should be stored."""
        return self._trace_all

    @property
    def trace_buffer_size_mb(self) -> int | float:
        """Returns the size of the trace buffer in megabytes."""
        return self._trace_buffer_size_mb

    @property
    def populate_app_call_resource(self) -> bool:
        """Indicates whether or not to populate app call resources."""
        return self._populate_app_call_resources

    def with_debug(self, func: Callable[[], str | None]) -> None:
        """
        Executes a function with debug mode temporarily enabled.
        """
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
        populate_app_call_resources: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Configures various settings for the application.

        :param debug: Whether debug mode is enabled.
        :param project_root: The path to the project root directory.
        :param trace_all: Whether to trace all operations. Defaults to False.
        :param trace_buffer_size_mb: The trace buffer size in megabytes. Defaults to 256.
        :param max_search_depth: The maximum depth to search for a specific file. Defaults to 10.
        :param populate_app_call_resources: Whether to populate app call resources. Defaults to True.
        :param logger: A custom logger to use. Defaults to AlgoKitLogger instance.
        """
        if logger is not None:
            self._logger = logger

        if debug is not None:
            self._debug = debug
            # Update logger's level so debug messages are processed only when debug is True.
            self._logger.setLevel(logging.DEBUG)

        if project_root is not None:
            self._project_root = project_root.resolve(strict=True)
        elif debug is not None and ALGOKIT_PROJECT_ROOT:
            self._project_root = Path(ALGOKIT_PROJECT_ROOT).resolve(strict=True)

        self._trace_all = trace_all
        self._trace_buffer_size_mb = trace_buffer_size_mb
        self._max_search_depth = max_search_depth
        self._populate_app_call_resources = populate_app_call_resources


config = UpdatableConfig()
