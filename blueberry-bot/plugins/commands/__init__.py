from nonebot import on_command,logger
from nonebot.rule import is_type
from nonebot.internal.adapter.bot import Bot

from nonebot.adapters.discord.commands import (
    CommandOption,
    on_slash_command,
)
import platform,psutil

def get_system_info()->str:
    sysinfo=[]
    uname=platform.uname()
    sysinfo.append(f"System Info")
    sysinfo.append(f"{uname.system} {uname.release} {uname.machine}, Python {platform.python_version()}")
    memory=psutil.virtual_memory()
    
    sysinfo.append(f"CPU: {psutil.cpu_count(False)}c{psutil.cpu_count()}t {psutil.cpu_freq().current:.0f}Mhz {psutil.cpu_percent():.1f}%, RAM: {(memory.total-memory.available)/(2<<29):.1f}/{memory.total/(2<<29):.1f}GiB")
    
    print(platform)
    return "\n".join(sysinfo)

slash = on_slash_command(
    name="sysinfo",
    description="显示运行此Bot的系统信息")
@slash.handle()
async def _():
    await slash.send(get_system_info())

cmd = on_command("sysinfo")
@cmd.handle()
async def _():
    await cmd.send(get_system_info())