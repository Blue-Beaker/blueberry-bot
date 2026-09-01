#!/usr/bin/env python3
"""
Client for BlueberryBot-Render server.
Connects to the Godot render server via HTTP (preferred) or WebSocket fallback,
sends a render request, and receives raw PNG data.

Binary parameters (e.g. thumbnail images) are base64-encoded with a ``base64://``
prefix so Godot's TextureHelper can decode them directly — no separate resource
server needed for binary data.
"""

import base64
import json
import asyncio
import time
from nonebot import logger

try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    raise

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    raise

from .config import Config
from .models import RenderArgs

try:
    from nonebot import get_plugin_config
    plugin_config = get_plugin_config(Config)
    
except Exception:
    plugin_config = Config()

_DEFAULT_URI = plugin_config.render_server_uri
_DEFAULT_TIMEOUT = plugin_config.render_server_timeout


def _parse_uri(uri: str) -> str:
    """解析 URI，返回 HTTP 渲染端点 URL。

    - ``ws://`` / ``wss://`` -> 原样返回（兼容旧配置，直接 WebSocket）
    - ``http://`` / ``https://`` -> 追加 ``/render`` 路径
    """
    scheme = uri.split("://", 1)[0].lower() if "://" in uri else "http"
    if scheme in ("ws", "wss"):
        return uri
    return uri.rstrip("/") + "/render"


class RenderAPI:
    """BlueberryBot-Render 客户端。

    封装与 Godot 渲染服务的通信。根据 ``uri`` 的 scheme 自动选择协议：
    - ``http://`` / ``https://`` -> HTTP POST /render（默认，推荐）
    - ``ws://`` / ``wss://`` -> WebSocket

    bytes 参数（如 thumbnail）自动转为 ``base64://`` 内联编码，
    Godot 的 TextureHelper 原生支持解码，无需额外资源服务器。

    Args:
        uri: Godot 渲染服务地址。
              例如 ``http://127.0.0.1:9081``（HTTP）或 ``ws://127.0.0.1:9080``（WebSocket）。
        timeout: 渲染超时时间（秒）
    """

    def __init__(
        self,
        uri: str = _DEFAULT_URI,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        self.timeout = timeout
        self._uri = _parse_uri(uri)
        self._is_ws = self._uri.startswith("ws://") or self._uri.startswith("wss://")

    async def _process_params(
        self,
        params: dict,
    ) -> dict:
        """Process render parameters, converting binary data to base64:// strings.

        - ``bytes`` values are base64-encoded with ``base64://`` prefix,
          so Godot's TextureHelper can decode them directly.
        - Strings are passed through as-is.
        """
        if not params:
            return {}

        result = dict(params)

        for key, value in result.items():
            if isinstance(value, bytes):
                # Godot 的 TextureHelper 原生支持 base64:// 前缀解码
                b64 = base64.b64encode(value).decode("ascii")
                result[key] = f"base64://{b64}"

        return result

    async def _render_http(self, scene: str, request_id: str,
                           params: dict | None = None,
                           _retries: int = 2) -> bytes | dict | None:
        """通过 HTTP POST /render 发送渲染请求，返回 PNG bytes 或错误 dict。

        所有 bytes 参数自动转为 ``base64://`` 内联编码，无需额外资源服务器。
        Godot 的 TextureHelper 原生支持 ``base64://`` 前缀解码。
        """
        for attempt in range(1, _retries + 1):
            try:
                request = {"scene": scene, "request_id": request_id}
                if params:
                    processed = await self._process_params(params)
                    request.update(processed)

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self._uri, json=request)

                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "")
                    if "image" in content_type or "application/octet-stream" in content_type:
                        return resp.content  # PNG bytes
                    return resp.json()  # 可能是 JSON 响应
                elif resp.status_code == 500:
                    # 服务端错误，重试
                    if attempt < _retries:
                        continue
                    return None
                else:
                    # 其他错误（400/404 等），不重试
                    try:
                        return resp.json()
                    except Exception:
                        return {"type": "error", "message": f"HTTP {resp.status_code}"}
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < _retries:
                    continue
                return None
        return None

    async def _render_websocket(self, scene: str, request_id: str,
                                params: dict | None = None,
                                _retries: int = 3) -> bytes | dict | None:
        """通过 WebSocket 发送渲染请求，作为 HTTP 失败时的回退方案。

        bytes 参数自动转为 ``base64://`` 内联编码。
        """
        for attempt in range(1, _retries + 1):
            try:
                request = {"scene": scene, "request_id": request_id}
                if params:
                    processed = await self._process_params(params)
                    request.update(processed)

                async with websockets.connect(
                    self._uri,
                    max_size=100 * 1024 * 1024,
                    max_queue=None,
                ) as ws:
                    await ws.send(json.dumps(request))

                    # 接收渲染结果
                    fragments: list[bytes] = []
                    is_text = False
                    async for fragment in ws.recv_streaming():
                        if isinstance(fragment, str):
                            is_text = True
                            fragments.append(fragment.encode())
                        else:
                            fragments.append(fragment)

                    raw = b"".join(fragments)
                    if not raw:
                        if attempt < _retries:
                            continue  # 空结果，重试
                        return None
                    if is_text:
                        return json.loads(raw.decode())
                    else:
                        return raw
            except OSError:
                if attempt < _retries:
                    continue  # 连接失败，重试
                return None
        return None

    async def _render(self, scene: str, request_id: str,
                      params: dict | None = None,
                      _retries: int = 3) -> bytes | dict | None:
        """发送渲染请求到 Godot 渲染服务，返回渲染结果。

        根据 ``uri`` 的 scheme 自动选择协议：
        - ``http://`` / ``https://`` -> HTTP POST /render
        - ``ws://`` / ``wss://`` -> WebSocket（兼容旧配置）

        bytes 参数自动转为 ``base64://`` 内联编码，Godot 的 TextureHelper 原生支持。
        """
        logger.info(f"Rendering scene {scene}...")
        time_ns=time.time_ns()
        if self._is_ws:
            result = await self._render_websocket(scene, request_id, params, _retries)
        result = await self._render_http(scene, request_id, params, _retries)

        logger.info(f"Render took {(time.time_ns()-time_ns)/1000000:.1f}ms.")
        return result

    async def render_text(self, request_id: str,
                               description: str) -> bytes | dict | None:
        """渲染 text 场景。
        """
        params = {k: v for k, v in locals().items()
                  if k not in ("self", "request_id") and v is not None}
        return await self._render("text_scene", request_id, params)
    
    async def render(self, args:RenderArgs) -> bytes | dict | None:
        """使用特定的RenderArgs渲染场景。
        """
        params = args.get_params()
        return await self._render(args.scene_type, args.request_id, params)

