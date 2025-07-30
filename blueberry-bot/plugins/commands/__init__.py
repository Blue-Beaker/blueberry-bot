from nonebot import on_command,logger
from nonebot.rule import is_type
from nonebot.internal.adapter.bot import Bot
from nonebot.adapters.minecraft.bot import Bot as MCBot


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

def get_help(is_mc:bool=False)->str:
    help_lines=[
        f"接受指令前缀: - &{' /' if not is_mc else ''}"
        "help 显示本帮助",
        "guess <start|giveup> 开始/放弃猜图",
        "guess <图名> 进行猜图",
        "sysinfo 显示运行此Bot的系统信息"
    ]
    if(is_mc):
        help_lines.append("tp 传送 (只能传送自己)")
    return "\n".join(help_lines)

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
    
slash = on_slash_command(
    name="help",
    description="显示运行此Bot的系统信息")
@slash.handle()
async def _():
    await slash.send(get_help())

cmd = on_command("help")
@cmd.handle()
async def _(bot):
    await cmd.send(get_help(isinstance(bot,MCBot)))