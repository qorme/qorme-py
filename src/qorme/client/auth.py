import asyncio

import httpx

from qorme.utils.datetime import utcnow


class AuthToken:
    """Represents an authentication token with its expiration time."""

    __slots__ = "value", "expires_at"

    def __init__(self, token: str, expires_at: int) -> None:
        self.update(token, expires_at)

    def update(self, token: str, expires_at: int):
        self.value = token
        self.expires_at = expires_at - 3

    def expired(self) -> bool:
        return self.expires_at < utcnow().timestamp()

    def __repr__(self):
        return f"AuthToken(token={self.value}, expires_at={self.expires_at})"


class Auth(httpx.Auth):
    """
    Handles authentication flow for the Qorme client,
    including token management and refreshing.
    """

    ApiKeyHeader = "X-Api-Key"
    UserAgentHeader = "User-Agent"
    SessionIdHeader = "X-Session-ID"
    AuthorizationHeader = "Authorization"

    def __init__(self, *, url: str, api_key: str, user_agent: str, session_id: str) -> None:
        self.url = url
        self.token = AuthToken("", 0)
        self.token_lock = asyncio.Lock()
        self.headers: dict[str, str] = {
            self.ApiKeyHeader: api_key,
            self.UserAgentHeader: user_agent,
            self.SessionIdHeader: session_id,
        }

    async def async_auth_flow(self, request: httpx.Request):
        async with self.token_lock:
            if self.token.expired():
                response = yield httpx.Request(method="post", url=self.url, headers=self.headers)
                await response.aread()
                data = response.json()
                self.token.update(data["token"], data["expires_at"])

        request.headers[self.AuthorizationHeader] = self.token.value
        yield request

    def sync_auth_flow(self, request: httpx.Request):
        raise RuntimeError("Cannot use an sync authentication class with httpx.AsyncClient")
