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
from pathlib import Path
import sys

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

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[2]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.bbot_render.config import Config
else:
    from .config import Config

try:
    from nonebot import get_plugin_config
    plugin_config = get_plugin_config(Config)
    
except Exception:
    plugin_config = Config()

_DEFAULT_URI = plugin_config.render_server_uri
_DEFAULT_TIMEOUT = plugin_config.render_server_timeout


def _parse_uri(uri: str) -> str:
    """解析 URI，返回 HTTP 渲染端点 URL。

    - ``ws://`` / ``wss://`` → 原样返回（兼容旧配置，直接 WebSocket）
    - ``http://`` / ``https://`` → 追加 ``/render`` 路径
    """
    scheme = uri.split("://", 1)[0].lower() if "://" in uri else "http"
    if scheme in ("ws", "wss"):
        return uri
    return uri.rstrip("/") + "/render"


class RenderAPI:
    """BlueberryBot-Render 客户端。

    封装与 Godot 渲染服务的通信。根据 ``uri`` 的 scheme 自动选择协议：
    - ``http://`` / ``https://`` → HTTP POST /render（默认，推荐）
    - ``ws://`` / ``wss://`` → WebSocket

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
        - ``http://`` / ``https://`` → HTTP POST /render
        - ``ws://`` / ``wss://`` → WebSocket（兼容旧配置）

        bytes 参数自动转为 ``base64://`` 内联编码，Godot 的 TextureHelper 原生支持。
        """
        if self._is_ws:
            return await self._render_websocket(scene, request_id, params, _retries)
        return await self._render_http(scene, request_id, params, _retries)

    async def render_player_info(self, request_id: str,
                                 playername: str,
                                 stars: int = 0,
                                 moons: int = 0,
                                 coins: int = 0,
                                 usercoins: int = 0,
                                 demons: int = 0,
                                 creatorpoints: int = 0,
                                 nondemons: int|str = 0,
                                 nonpemons: int|str = 0,
                                 c_demons: int = 0,
                                 pemons: int = 0,**kwargs) -> bytes | dict | None:
        """渲染 player_info 场景。

        参数说明参考 player_info_renderer.gd。
        """
        params = {k: v for k, v in locals().items()
                  if k not in ("self", "request_id") and v is not None}
        params.update(kwargs)
        return await self._render("player_info", request_id, params)

    async def render_demons(self, request_id: str,
                            c_ezd: int = 0,
                            c_med: int = 0,
                            c_hdd: int = 0,
                            c_insd: int = 0,
                            c_exd: int = 0,
                            c_all: int = 0,
                            p_ezd: int = 0,
                            p_med: int = 0,
                            p_hdd: int = 0,
                            p_insd: int = 0,
                            p_exd: int = 0,
                            p_all: int = 0,
                            weekly: int = 0,
                            gauntlet: int = 0) -> bytes | dict | None:
        """渲染 demons 场景（恶魔完成统计）。

        参数说明参考 demons_renderer.gd。
        """
        params = {k: v for k, v in locals().items()
                  if k not in ("self", "request_id") and v is not None}
        return await self._render("demons", request_id, params)

    async def render_nondemons(self, request_id: str,
                               c_auto: int = 0,
                               c_easy: int = 0,
                               c_normal: int = 0,
                               c_hard: int = 0,
                               c_harder: int = 0,
                               c_insane: int = 0,
                               c_all: int|str = 0,
                               p_auto: int = 0,
                               p_easy: int = 0,
                               p_normal: int = 0,
                               p_hard: int = 0,
                               p_harder: int = 0,
                               p_insane: int = 0,
                               p_all: int|str = 0,
                               daily: int = 0,
                               gauntlet: int = 0) -> bytes | dict | None:
        """渲染 nondemons 场景（非恶魔完成统计）。

        参数说明参考 nondemons_renderer.gd。
        """
        params = {k: v for k, v in locals().items()
                  if k not in ("self", "request_id") and v is not None}
        return await self._render("nondemons", request_id, params)

    async def render_level(self, request_id: str,
            level_name: str = "",
            creator: str = "",
            song_id: int = 0,
            song_name: str = "",
            song_author: str = "",
            weight: str = "",
            pemonlist: str = "",
            stars: int = 0,
            length: str = "",
            downloads: int = 0,
            orbs: int = 0,
            level_id: int = 0,
            # Texture resources — accepts raw bytes or URL string
            thumbnail: bytes | str = b"",
            difficulty: int = 0,
            feature_level: int = 0,
            is_plat: bool = False,
            diffchart_tier: str = '',
            checkpoints: str = '',
            diffchart_tags: str = '',
            description: str = '',
            length2: str = '',
            bronze_coins: bool = False,
            likes: int = 0,
            # Coins
            coins: int = 0,
            scene_type: str = "level",
            **kwargs) -> bytes | dict | None:
        """渲染 level 场景（关卡信息）。

        可直接传入 bytes 类型的 thumbnail，框架自动转为 base64:// 内联编码。
        """
        params = {k: v for k, v in locals().items()
                  if k not in ("self", "request_id", "scene_type", "kwargs") and v is not None and v != b""}
        params.update(kwargs)
        return await self._render(scene_type, request_id, params)

    async def render_text(self, request_id: str,
                               description: str) -> bytes | dict | None:
        """渲染 text 场景。
        """
        params = {k: v for k, v in locals().items()
                  if k not in ("self", "request_id") and v is not None}
        return await self._render("text_scene", request_id, params)



async def _test_main():
    """测试功能：发送示例请求并保存结果"""
    api = RenderAPI()

    print("=== Testing player_info ===")
    result = await api.render_player_info(
        "test-001",
        playername="Robtop",
        stars=1337,
        moons=42,
        coins=21,
        usercoins=999,
        demons=77,
        creatorpoints=500,
        nondemons=100,
        nonpemons=88,
        c_demons=100,
        pemons=100
    )
    _save_result(result, "render_player_info.png")

    print("\n=== Testing demons ===")
    result = await api.render_demons(
        "test-002",
        c_ezd=10, c_med=20, c_hdd=15, c_insd=8, c_exd=5, c_all=58,
        p_ezd=5, p_med=8, p_hdd=3, p_insd=1, p_exd=0, p_all=17,
        weekly=3, gauntlet=2,
    )
    _save_result(result, "render_demons.png")

    print("\n=== Testing nondemons ===")
    result = await api.render_nondemons(
        "test-003",
        c_auto=5, c_easy=30, c_normal=50, c_hard=25, c_harder=10, c_insane=3, c_all=123,
        p_auto=3, p_easy=15, p_normal=20, p_hard=8, p_harder=2, p_insane=0, p_all=48,
        daily=1,
    )
    _save_result(result, "render_nondemons.png")
    
    print("\n=== Testing text ===")
    result = await api.render_text(
        "test-004","a98u8912u38uj0c vnduiy39ru2043jr"
    )
    _save_result(result, "render_text.png")


def _save_result(result: bytes | dict | None, filename: str):
    if result is None:
        print("No response (connection failed)")
        return
    if isinstance(result, bytes):
        with open(filename, "wb") as f:
            f.write(result)
        print(f"Image saved as '{filename}' ({len(result)} bytes)")
    elif isinstance(result, dict) and result.get("type") == "error":
        print(f"Error: {result.get('message')}")
    else:
        print(f"Unexpected response: {result}")


if __name__ == "__main__":
    asyncio.run(_test_main())
