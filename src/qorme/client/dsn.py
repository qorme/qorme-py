from urllib.parse import urlsplit


class DSNError(ValueError):
    """Invalid DSN."""


class DSN:
    __slots__ = "url", "api_key"

    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key

    @classmethod
    def parse(cls, dsn: str) -> "DSN":
        parts = urlsplit(dsn)
        if parts.scheme != "https":
            raise DSNError("Invalid scheme %s, only https is supported", parts.scheme)
        if not (api_key := parts.username):
            raise DSNError("Missing API key")
        if not (host := parts.hostname):
            raise DSNError("Missing hostname")
        return cls(f"https://{host}:{parts.port or 443}", api_key)

    def __repr__(self):
        return f"DSN(url={self.url}, api_key=redacted)"
