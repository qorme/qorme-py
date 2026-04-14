import unittest

import httpx

from qorme.client.auth import Auth

from ..mock import MockServer


class TestAuth(unittest.IsolatedAsyncioTestCase):
    # 1. behavior when token has expired
    # 2. when token is valid
    # 3. Check headers
    # 4. When multiple coroutines call simultaneously
    async def test_auth_flow(self):
        auth = Auth(
            url="http://test.com/auth/", api_key="key", user_agent="test", session_id="1234"
        )
        client = httpx.AsyncClient(auth=auth, transport=httpx.MockTransport(MockServer()))

        response = await client.get("http://test.com/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"text": "Hello, world!"})
