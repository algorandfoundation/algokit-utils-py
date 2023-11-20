import logging
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class UpdatableConfig:
    def __init__(self) -> None:
        self._debug: bool = False
        self._project_root: str | None = None
        self._trace_all: bool = False
        self._trace_buffer_size_mb: int = 512  # megabytes
        self._max_search_depth: int = 10

    def _load_project_root(self) -> None:
        # search for a filename named .algokit.toml starting from current file's directory and going up at most 4 levels
        # if not found, set None
        current_file = Path(__file__).resolve()
        for _ in range(self._max_search_depth):
            logger.info("Looking inside: " + str(current_file))
            logger.info("Looking inside (parent): " + str(current_file.parent))
            current_file = current_file.parent
            if (current_file / ".algokit.toml").exists():
                self._project_root = str(current_file)
                return

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def project_root(self) -> Path | None:
        return Path(self._project_root) if self._project_root else None

    @property
    def trace_all(self) -> bool:
        return self._trace_all

    def with_debug(self, lambda_func: Callable[[], None | str]) -> None:
        original = self._debug
        try:
            self._debug = True
            lambda_func()
        finally:
            self._debug = original

    def configure(
        self,
        *,
        debug: bool,
        project_root: str | None = None,
        trace_all: bool = False,
        trace_buffer_size_mb: int = 512,
        max_search_depth: int = 10
    ) -> None:
        if debug is not None:
            self._debug = debug

        if project_root:
            self._project_root = str(Path(project_root).resolve(strict=True))
        elif debug:
            self._load_project_root()

        self._trace_all = trace_all
        self._trace_buffer_size_mb = trace_buffer_size_mb
        self._max_search_depth = max_search_depth


config = UpdatableConfig()
