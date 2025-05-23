
from nonebot.adapters.discord.commands import (
    CommandOption,
    on_slash_command,
)
import platform

def get_system_info()->str:
    sysinfo=[]
    print(platform)
    return "\n".join(sysinfo)

matcher = on_slash_command(
    name="sysinfo",
    description="显示系统信息")
@matcher.handle()
async def _():
    await matcher.send("Test Feedback!")

