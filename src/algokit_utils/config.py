from collections.abc import Callable


class UpdatableConfig:
    def __init__(self) -> None:
        self._debug: bool = False

    @property
    def debug(self) -> bool:
        return self._debug

    def with_debug(self, lambda_func: Callable[[], None | str]) -> None:
        original = self._debug
        try:
            self._debug = True
            lambda_func()
        finally:
            self._debug = original

    def configure(self, *, debug: bool) -> None:
        if debug is not None:
            self._debug = debug


config = UpdatableConfig()
