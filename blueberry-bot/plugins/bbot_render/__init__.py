#!/usr/bin/env python3
"""
Client for BlueberryBot-Render WebSocket server.
Connects to the Godot WebSocket server, sends a render request, and receives raw PNG data.
Large binary parameters (e.g. thumbnail images) are automatically served via a local HTTP
resource server to avoid hitting Godot's inbound WebSocket message size limit.
"""

import json
import asyncio
from pathlib import Path
import sys

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
    from plugins.bbot_render.resource_server import ResourceServer
else:
    from .config import Config
    from .resource_server import ResourceServer

try:
    from nonebot import get_plugin_config
    plugin_config = get_plugin_config(Config)
except Exception:
    plugin_config = Config()

_DEFAULT_URI = "ws://localhost:9080"
_DEFAULT_TIMEOUT = 30.0
# Parameters with values larger than this (bytes) will be served via HTTP instead
_RESOURCE_THRESHOLD = 50 * 1024  # 50 KB


class RenderAPI:
    """BlueberryBot-Render WebSocket 客户端。

    封装与 Godot 渲染服务的 WebSocket 通信，管理连接参数。
    大字段（如 thumbnail 图片）自动通过本地 HTTP 服务提供 URL 给 Godot，
    避免超出 Godot 的 WebSocket 入站消息大小限制。

    Args:
        uri: Godot WebSocket 服务端地址
        timeout: 渲染超时时间（秒）
        resource_url: 本地资源 HTTP 服务 URL，如 http://127.0.0.1:9081/resources
    """

    def __init__(
        self,
        uri: str = _DEFAULT_URI,
        timeout: float = _DEFAULT_TIMEOUT,
        resource_url: str | None = None,
        resource_alt_url: str | None = None,
    ):
        self.uri = uri
        self.timeout = timeout
        self._resource_server: ResourceServer | None = None
        self._resource_url = resource_url or plugin_config.render_resource_url
        self._resource_alt_url = resource_alt_url if resource_alt_url is not None else plugin_config.render_resource_alt_url

    async def _ensure_resource_server(self) -> ResourceServer:
        if self._resource_server is None:
            self._resource_server = ResourceServer(
                base_url=self._resource_url,
                alt_url=self._resource_alt_url,
            )
            await self._resource_server.start()
        return self._resource_server

    async def _process_params(
        self,
        params: dict,
    ) -> dict:
        """Process render parameters, replacing large binary values with HTTP URLs."""
        if not params:
            return {}

        server = await self._ensure_resource_server()
        result = dict(params)

        for key, value in result.items():
            if isinstance(value, bytes) and len(value) > _RESOURCE_THRESHOLD:
                url = server.add_resource(value, suffix=".png")
                result[key] = url
            elif isinstance(value, str) and len(value) > _RESOURCE_THRESHOLD:
                url = server.add_resource(value.encode("utf-8"), suffix=".txt")
                result[key] = url

        return result

    async def _render(self, scene: str, request_id: str,
                      params: dict | None = None) -> bytes | dict | None:
        """发送渲染请求到 Godot 渲染服务，返回渲染结果。

        大字段（如 thumbnail bytes）自动替换为 HTTP URL，
        Godot 通过本地 HTTP 服务获取，避免入站消息过大。
        """
        try:
            request = {"scene": scene, "request_id": request_id}
            if params:
                request.update(await self._process_params(params))

            async with websockets.connect(
                self.uri,
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
                if is_text:
                    return json.loads(raw.decode())
                else:
                    return raw
        except OSError:
            return None

    async def render_player_info(self, request_id: str,
                                 playername: str,
                                 stars: int = 0,
                                 moons: int = 0,
                                 coins: int = 0,
                                 usercoins: int = 0,
                                 demons: int = 0,
                                 creatorpoints: int = 0,
                                 nondemons: int = 0,
                                 nonpemons: int = 0,
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
                               c_all: int = 0,
                               p_auto: int = 0,
                               p_easy: int = 0,
                               p_normal: int = 0,
                               p_hard: int = 0,
                               p_harder: int = 0,
                               p_insane: int = 0,
                               p_all: int = 0,
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

        可直接传入 bytes 类型的 thumbnail，框架会自动通过 HTTP 提供给 Godot。
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
