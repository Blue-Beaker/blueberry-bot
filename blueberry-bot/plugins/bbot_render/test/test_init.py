import pytest
from plugins.bbot_render import RenderAPI


@pytest.mark.asyncio
async def test_render_main():
    """测试功能：发送示例请求并保存结果"""
    api = RenderAPI()
    from plugins.bbot_render.models import PlayerInfoRenderArgs,DemonsRenderArgs,NonDemonsRenderArgs

    print("=== Testing player_info ===")
    args_player=PlayerInfoRenderArgs("test-001")
    args_player.update_args(
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
    result = await api.render(args_player)
    _save_result(result, "render_player_info.png")

    print("\n=== Testing demons ===")
    args_demons=DemonsRenderArgs("test-002")
    args_demons.update_args(
        c_ezd=10, c_med=20, c_hdd=15, c_insd=8, c_exd=5, c_all=58,
        p_ezd=5, p_med=8, p_hdd=3, p_insd=1, p_exd=0, p_all=17,
        weekly=3, gauntlet=2,
    )
    result = await api.render(args_demons)
    _save_result(result, "render_demons.png")

    print("\n=== Testing nondemons ===")
    args_nondemons=NonDemonsRenderArgs("test-003")
    args_nondemons.update_args(
        c_auto=5, c_easy=30, c_normal=50, c_hard=25, c_harder=10, c_insane=3, c_all=123,
        p_auto=3, p_easy=15, p_normal=20, p_hard=8, p_harder=2, p_insane=0, p_all=48,
        daily=1,
    )
    result = await api.render(args_nondemons)
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
