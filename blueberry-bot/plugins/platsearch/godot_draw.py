#!/usr/bin/env python3
"""
Client for BlueberryBot-Render WebSocket server.
Connects to the Godot WebSocket server, sends a render request, and receives raw PNG data.
"""

import json
import asyncio

from nonebot import logger

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    raise

_DEFAULT_URI = "ws://localhost:9080"
_DEFAULT_TIMEOUT = 30.0


class RenderAPI:
    """BlueberryBot-Render WebSocket 客户端。

    封装与 Godot 渲染服务的 WebSocket 通信，管理连接参数。
    """

    def __init__(self, uri: str = _DEFAULT_URI, timeout: float = _DEFAULT_TIMEOUT):
        self.uri = uri
        self.timeout = timeout

    async def _render(self, scene: str, request_id: str,
                      params: dict | None = None) -> bytes | dict | None:
        """发送渲染请求到 Godot 渲染服务，返回渲染结果。

        Args:
            scene: 场景名称，如 "player_info"
            request_id: 请求标识符
            params: 场景参数字典，不含 scene 和 request_id

        Returns:
            如果服务返回二进制数据，返回 bytes（PNG 图片）
            如果服务返回文本，解析为 dict 后返回（可能是错误信息）
        """
        # logger.debug(params)
        try:
            request = {"scene": scene, "request_id": request_id}
            if params:
                request.update(params)

            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps(request))
                data = await asyncio.wait_for(ws.recv(), timeout=self.timeout)

                if isinstance(data, bytes):
                    return data
                else:
                    return json.loads(data)
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

    async def render_level(self,request_id:str,
            level_name: str="",
            creator: str="",
            diff_name: str="",
            song_name: str="",
            weight: str="",
            pemonlist: str="",
            stars: int=0,
            length: str="",
            downloads: int=0,
            orbs: int=0,
            level_id: int=0,
            # Texture resources
            thumbnail: str="",
            diff_icon: str="",
            feature_icon: str="",
            star_or_moon: str="",
            diffchart_icon: str="",
            # Coins
            coins: int=0,scene_type: str="level") -> bytes | dict | None:
        """渲染 level 场景（关卡信息）。
        """
        params = {k: v for k, v in locals().items()
                  if k not in ("self", "request_id") and v is not None}
        return await self._render(scene_type, request_id, params)

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
