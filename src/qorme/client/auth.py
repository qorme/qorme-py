import asyncio

import httpx

from qorme.utils.datetime import utcnow


class AuthToken:
    __slots__ = "token", "expires_at"

    def __init__(self, token: str, expires_at: int) -> None:
        self.update(token, expires_at)

    def update(self, token: str, expires_at: int):
        self.token = token
        self.expires_at = expires_at - 3

    def expired(self) -> bool:
        return self.expires_at < utcnow().timestamp()

    def __repr__(self):
        return f"AuthToken(token={self.token}, expires_at={self.expires_at})"


class Auth(httpx.Auth):
    ApiKeyHeader = "X-Api-Key"
    UserAgentHeader = "User-Agent"
    SessionIdHeader = "X-Session-ID"
    AuthorizationHeader = "Authorization"

    def __init__(self, *, url, api_key, user_agent, session_id):
        self.url = url
        self.headers = {
            self.ApiKeyHeader: api_key,
            self.UserAgentHeader: user_agent,
            self.SessionIdHeader: session_id,
        }
        self.token = AuthToken("", 0)
        self.token_lock = asyncio.Lock()

    async def async_auth_flow(self, request):
        async with self.token_lock:
            if self.token.expired():
                response = yield httpx.Request(method="post", url=self.url, headers=self.headers)
                await response.aread()
                data = response.json()
                self.token.update(data["token"], data["expires_at"])

        request.headers[self.AuthorizationHeader] = self.token.token
        yield request

    def sync_auth_flow(self, request):
        raise RuntimeError("Cannot use an sync authentication class with httpx.AsyncClient")
