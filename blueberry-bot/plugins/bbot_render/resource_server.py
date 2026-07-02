#!/usr/bin/env python3
"""
Temporary HTTP server that serves binary resources to Godot.

When a render parameter contains large binary data (e.g. thumbnail images),
it is served via this server and the parameter value is replaced with an HTTP URL.
This avoids hitting Godot's inbound WebSocket message size limit.
"""

import asyncio
import uuid
from urllib.parse import urlparse


def _ensure_scheme(url: str) -> str:
    """Prepend http:// if no scheme is present."""
    if url and "://" not in url:
        return f"http://{url}"
    return url


class ResourceServer:
    """Temporary HTTP server that serves binary resources to Godot.

    When a render parameter contains large binary data (e.g. thumbnail images),
    it is served via this server and the parameter value is replaced with an HTTP URL.
    This avoids hitting Godot's inbound WebSocket message size limit.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9081/resources",
        alt_url: str = "",
    ):
        base_url = _ensure_scheme(base_url)
        parsed = urlparse(base_url)
        self._host = parsed.hostname or "127.0.0.1"
        self._port = parsed.port or 9081
        self._url_prefix = parsed.path.rstrip("/") or "/resources"
        self._alt_url = _ensure_scheme(alt_url).rstrip("/")
        self._server: asyncio.AbstractServer | None = None
        self._resources: dict[str, bytes] = {}

    @property
    def base_url(self) -> str:
        """URL exposed to Godot — uses alt_url if set, otherwise the local address."""
        if self._alt_url:
            return self._alt_url
        return f"http://{self._host}:{self._port}{self._url_prefix}"

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_connection, host=self._host, port=self._port
        )
        print(f"[bbot_render] Resource server started on {self.base_url}")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    def add_resource(self, data: bytes, suffix: str = ".png") -> str:
        """Register binary data and return its HTTP URL."""
        filename = f"{uuid.uuid4().hex}{suffix}"
        self._resources[filename] = data
        return f"{self.base_url}/{filename}"

    def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> asyncio.Task:
        return asyncio.create_task(self._handle_request(reader, writer))

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=30)
            if not request_line:
                return

            parts = request_line.decode("utf-8", errors="replace").strip().split(" ")
            if len(parts) < 2:
                await self._respond(writer, 400, b"Bad Request")
                return

            method = parts[0]
            path = parts[1]

            # Read and discard headers
            while True:
                header_line = await reader.readline()
                if header_line in (b"\r\n", b"\n", b""):
                    break

            if method != "GET":
                await self._respond(writer, 405, b"Method Not Allowed")
                return

            # Extract filename from path: <url_prefix>/<filename>
            prefix = self._url_prefix.strip("/")
            path_parts = path.strip("/").split("/")
            if len(path_parts) < 2 or path_parts[0] != prefix:
                await self._respond(writer, 404, b"Not Found")
                return

            filename = path_parts[1]
            data = self._resources.get(filename)
            if data is None:
                await self._respond(writer, 404, b"Not Found")
                return

            await self._respond(
                writer, 200, data,
                extra_headers={"Content-Type": "image/png"},
            )
        except (asyncio.TimeoutError, Exception):
            try:
                await self._respond(writer, 500, b"Internal Server Error")
            except Exception:
                pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    @staticmethod
    async def _respond(
        writer: asyncio.StreamWriter,
        status: int,
        body: bytes,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        reason = {200: "OK", 400: "Bad Request", 404: "Not Found",
                  405: "Method Not Allowed", 500: "Internal Server Error"}.get(status, "Unknown")
        headers = f"HTTP/1.1 {status} {reason}\r\nContent-Length: {len(body)}\r\n"
        if extra_headers:
            for k, v in extra_headers.items():
                headers += f"{k}: {v}\r\n"
        headers += "Connection: close\r\n\r\n"
        writer.write(headers.encode("utf-8") + body)
        await writer.drain()
