import logging
import os
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Environment variable to override the project root
ALGOKIT_PROJECT_ROOT = os.getenv("ALGOKIT_PROJECT_ROOT")
ALGOKIT_CONFIG_FILENAME = ".algokit.toml"


class UpdatableConfig:
    """Class to manage and update configuration settings for the AlgoKit project.

    Attributes:
        debug (bool): Indicates whether debug mode is enabled.
        project_root (Path | None): The path to the project root directory.
        trace_all (bool): Indicates whether to trace all operations.
        trace_buffer_size_mb (int): The size of the trace buffer in megabytes.
        max_search_depth (int): The maximum depth to search for a specific file.
    """

    def __init__(self) -> None:
        self._debug: bool = False
        self._project_root: Path | None = None
        self._trace_all: bool = False
        self._trace_buffer_size_mb: int | float = 256  # megabytes
        self._max_search_depth: int = 10
        self._configure_project_root()

    def _configure_project_root(self) -> None:
        """Configures the project root by searching for a specific file within a depth limit."""
        current_path = Path(__file__).resolve()
        for _ in range(self._max_search_depth):
            logger.debug(f"Searching in: {current_path}")
            if (current_path / ALGOKIT_CONFIG_FILENAME).exists():
                self._project_root = current_path
                break
            current_path = current_path.parent

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

    def with_debug(self, func: Callable[[], str | None]) -> None:
        """Executes a function with debug mode temporarily enabled."""
        original_debug = self._debug
        try:
            self._debug = True
            func()
        finally:
            self._debug = original_debug

    def configure(  # noqa: PLR0913
        self,
        *,
        debug: bool,
        project_root: Path | None = None,
        trace_all: bool = False,
        trace_buffer_size_mb: float = 256,
        max_search_depth: int = 10,
    ) -> None:
        """
        Configures various settings for the application.
        Please note, when `project_root` is not specified, by default config will attempt to find the `algokit.toml` by
        scanning the parent directories according to the `max_search_depth` parameter.
        Alternatively value can also be set via the `ALGOKIT_PROJECT_ROOT` environment variable.
        If you are executing the config from an algokit compliant project, you can simply call
        `config.configure(debug=True)`.

        Args:
            debug (bool): Indicates whether debug mode is enabled.
            project_root (Path | None, optional): The path to the project root directory. Defaults to None.
            trace_all (bool, optional): Indicates whether to trace all operations. Defaults to False. Which implies that
                only the operations that are failed will be traced by default.
            trace_buffer_size_mb (float, optional): The size of the trace buffer in megabytes. Defaults to 512mb.
            max_search_depth (int, optional): The maximum depth to search for a specific file. Defaults to 10.

        Returns:
            None
        """

        self._debug = debug

        if project_root:
            self._project_root = project_root.resolve(strict=True)
        elif debug and ALGOKIT_PROJECT_ROOT:
            self._project_root = Path(ALGOKIT_PROJECT_ROOT).resolve(strict=True)

        self._trace_all = trace_all
        self._trace_buffer_size_mb = trace_buffer_size_mb
        self._max_search_depth = max_search_depth


config = UpdatableConfig()
