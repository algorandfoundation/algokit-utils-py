# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field


@dataclass(slots=True)
class ClientConfig:
    """Runtime configuration for KmdClient."""

    base_url: str = "http://localhost:7833"
    token: str | None = None
    token_header: str = "X-KMD-API-Token"
    timeout: float | None = 30.0
    verify: bool | str = True
    extra_headers: dict[str, str] = field(default_factory=dict)

    def resolve_headers(self) -> dict[str, str]:
        headers = dict(self.extra_headers)
        if self.token:
            headers[self.token_header] = self.token
        return headers
