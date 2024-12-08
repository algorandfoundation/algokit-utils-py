from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class SendParams:
    max_rounds_to_wait: int | None = None
    suppress_log: bool | None = None
    populate_app_call_resources: bool | None = None
