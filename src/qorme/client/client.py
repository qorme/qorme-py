from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING
from uuid import uuid4

from qorme import __version__ as qorme_version

from .dsn import DSN

if TYPE_CHECKING:
    import httpx

    from qorme.utils.async_worker import AsyncWorker
    from qorme.utils.config import Config


logger = logging.getLogger(__name__)


class Client:
    """
    HTTP client for communicating with the Qorme server, handling authentication,
    retries, requests, and Server-Sent Events (SSE) connections.
    """

    user_agent = f"Qorme-Python/{qorme_version}"

    def __init__(
        self,
        config: Config,
        async_worker: AsyncWorker,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
    ):
        self.dsn = DSN.parse(config.dsn)
        self.config = config
        self.session_id = uuid4().hex
        self.async_worker = async_worker
        self._httpx_client: httpx.AsyncClient | None = None
        self._transport = transport  # Transport to wrap, used for testing with mock transport

    @property
    def httpx_client(self) -> httpx.AsyncClient:
        if self._httpx_client is None:
            import httpx
            import httpx_retries

            from .auth import Auth

            auth = Auth(
                url=f"{self.dsn.url}/auth/",
                api_key=self.dsn.api_key,
                user_agent=self.user_agent,
                session_id=self.session_id,
            )
            retry = httpx_retries.Retry(
                total=self.config.retry.attempts,
                backoff_factor=self.config.retry.backoff_factor,
                backoff_jitter=self.config.retry.backoff_jitter,
            )
            if not (transport := self._transport):
                # Doing this because verify isn't respect by httpx_retries.RetryTransport
                transport = httpx.AsyncHTTPTransport(
                    http2=self.config.http2, verify=self.config.verify_ssl
                )
            self._httpx_client = httpx.AsyncClient(
                auth=auth,
                base_url=self.dsn.url,
                timeout=self.config.request_timeout,
                headers={"User-Agent": self.user_agent},
                transport=httpx_retries.RetryTransport(transport=transport, retry=retry),
            )
        return self._httpx_client

    async def request(self, **kwargs) -> httpx.Response:
        try:
            response = await self.httpx_client.request(**kwargs)
            response.raise_for_status()
        except Exception:
            logger.exception("Qorme client request error", exc_info=True)
            raise
        else:
            return response

    def get(self, **kwargs):
        task = self.request(method="get", **kwargs)
        return self.async_worker.submit(task)

    def post(self, **kwargs):
        task = self.request(method="post", **kwargs)
        return self.async_worker.submit(task)

    async def _sse(
        self,
        path: str,
        handler,  # TODO: Define handler protocol type
        max_retries: int = 5,
        retry_interval: float = 10.0,
        method: str = "GET",
        **kwargs,
    ) -> None:
        import httpx
        from httpx_sse import aconnect_sse

        num_retries = 0
        headers = kwargs.pop("headers", {})
        logger.info("Establishing SSE connection at %s", path)

        try:
            while num_retries < max_retries:
                logger.info("Attempting SSE connection, attempt=%d", num_retries)
                headers["Last-Event-ID"] = handler.get_last_event_id()

                try:
                    async with aconnect_sse(
                        self.httpx_client, method, path, headers=headers, **kwargs
                    ) as event_source:
                        handler.on_sse_connect()
                        try:
                            async for event in event_source.aiter_sse():
                                await handler.on_event(event)
                        finally:
                            handler.on_sse_disconnect()
                except httpx.TransportError:
                    logger.info("SSE transport error", exc_info=True)
                    if num_retries != 0:
                        # Exponential backoff after first unsuccesful attempt
                        await asyncio.sleep(retry_interval * (1 << (num_retries - 1)))
                    num_retries += 1
                else:
                    logger.info("SSE stream ended cleanly, reconnecting immediately")
                    num_retries = 0  # Reset on clean disconnect
        except asyncio.CancelledError:
            logger.debug("SSE connection task cancelled")
            raise
        except Exception:
            logger.exception("SSE connection encountered unexpected error", exc_info=True)
            raise
        finally:
            handler.on_sse_exit()
            logger.info("SSE connection at %s dropped (num-retries=%d)", path, num_retries)

    def sse(self, *args, **kwargs):
        return self.async_worker.submit(self._sse(*args, **kwargs))

    def close(self):
        if not (client := self._httpx_client):
            return

        if not self.async_worker.is_running():
            self._httpx_client = None
            return

        try:
            fut = self.async_worker.submit(client.aclose())
            fut.result(timeout=self.config.shutdown_timeout)
        except TimeoutError:
            fut.cancel()
            logger.exception("Timeout error closing httpx client")
        except Exception:
            logger.exception("Error closing httpx client", exc_info=True)
        finally:
            self._httpx_client = None
