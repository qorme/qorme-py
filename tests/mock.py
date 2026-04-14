import httpx

from qorme.client.auth import Auth
from qorme.utils.datetime import utcnow


class MockServer:
    def __init__(self, *, token: str = "test-token", event_stream=None):
        self.token = token
        self.event_stream = event_stream
        self.requests = []

    def __call__(self, request: httpx.Request):
        self.requests.append(request)
        if request.url.path == "/auth/" and request.method == "POST":
            # TODO: Check headers
            return httpx.Response(
                200, json={"token": self.token, "expires_at": utcnow().timestamp() + 60}
            )
        if request.headers.get(Auth.AuthorizationHeader) != self.token:
            return httpx.Response(401)
        if request.url.path == "/" and request.method == "GET":
            return httpx.Response(200, json={"text": "Hello, world!"})
        if request.url.path == "/sse/":
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                stream=self.event_stream(),
            )
        if request.url.path == "/ingest/" and request.method == "POST":
            return httpx.Response(200)
        return httpx.Response(404)
