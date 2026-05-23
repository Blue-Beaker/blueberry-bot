#!/usr/bin/env python3
"""
Client for BlueberryBot-Render WebSocket server.
Connects to the Godot WebSocket server, sends a render request, and receives raw PNG data.
"""

import json
import asyncio

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    raise

_DEFAULT_URI="ws://localhost:9080"

async def render(scene: str, request_id: str, params: dict | None = None,
                 uri: str = _DEFAULT_URI,
                 timeout: float = 30.0) -> bytes | dict | None:
    try:
        """发送渲染请求到 Godot 渲染服务，返回渲染结果。

        Args:
            scene: 场景名称，如 "player_info"
            request_id: 请求标识符
            params: 场景参数字典，不含 scene 和 request_id
            uri: WebSocket 服务器地址
            timeout: 等待响应的超时时间（秒）

        Returns:
            如果服务返回二进制数据，返回 bytes（PNG 图片）
            如果服务返回文本，解析为 dict 后返回（可能是错误信息）
        """
        request = {"scene": scene, "request_id": request_id}
        if params:
            request.update(params)

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps(request))
            data = await asyncio.wait_for(ws.recv(), timeout=timeout)

            if isinstance(data, bytes):
                return data
            else:
                return json.loads(data)
    except OSError:
        return None


async def render_player_info(request_id: str,
                             playername: str,
                             stars: int = 0,
                             moons: int = 0,
                             coins: int = 0,
                             usercoins: int = 0,
                             demons: int = 0,
                             uri: str = _DEFAULT_URI,
                             timeout: float = 30.0) -> bytes | dict | None:
    """渲染 player_info 场景。

    Args:
        request_id: 请求标识符
        playername: 玩家名称
        stars: 星星数
        moons: 月亮数
        coins: 硬币数
        usercoins: 用户硬币数
        demons: 恶魔数
        uri: WebSocket 服务器地址
        timeout: 等待响应的超时时间（秒）

    Returns:
        同 render()
    """
    params = {k: v for k, v in locals().items()
              if k not in ("request_id", "uri", "timeout") and v is not None}
    return await render("player_info", request_id, params, uri=uri, timeout=timeout)


async def _test_main():
    """测试功能：发送一个示例请求并保存结果"""
    print(f"Connecting to ws://localhost:9080 ...")
    result = await render_player_info(
        "test-001",
        playername="Robtop",
        stars=1337,
        moons=42,
        coins=21,
        usercoins=999,
        demons=77,
    )
    print(f"Received data: {len(result) if isinstance(result, bytes) else result}")

    if isinstance(result, bytes):
        filename = "render_test-001.png"
        with open(filename, "wb") as f:
            f.write(result)
        print(f"Image saved as '{filename}' ({len(result)} bytes)")
    elif isinstance(result, dict) and result.get("type") == "error":
        print(f"Error: {result.get('message')}")
    else:
        print(f"Unexpected response: {result}")


if __name__ == "__main__":
    asyncio.run(_test_main())
