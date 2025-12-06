# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field


@dataclass(slots=True)
class ClientConfig:
    """Runtime configuration for IndexerClient.

    Attributes:
        base_url: Base URL for the API endpoint.
        token: Optional authentication token.
        token_header: Header name for the authentication token.
        timeout: Request timeout in seconds. Set to None for no timeout.
        verify: SSL certificate verification. Can be a boolean or path to CA bundle.
        extra_headers: Additional headers to include in all requests.
        max_retries: Maximum number of retry attempts for transient failures.
            Set to 0 to disable retries. Default is 4 (5 total attempts).
            Note: Retries are automatically disabled when a custom http_client
            is provided to avoid conflicts with the client's own retry mechanism.
    """

    base_url: str = "http://localhost:8980"
    token: str | None = None
    token_header: str = "X-Indexer-API-Token"
    timeout: float | None = 30.0
    verify: bool | str = True
    extra_headers: dict[str, str] = field(default_factory=dict)
    max_retries: int = 4

    def resolve_headers(self) -> dict[str, str]:
        headers = dict(self.extra_headers)
        if self.token:
            headers[self.token_header] = self.token
        return headers
