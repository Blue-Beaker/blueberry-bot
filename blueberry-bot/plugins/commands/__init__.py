from nonebot import on_command,logger,get_plugin_config,get_loaded_plugins,get_driver
from nonebot.rule import is_type
from nonebot.internal.adapter import Bot,Event,Message
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

def get_all_help(bot:Bot,event:Event)->str:
    is_mc=isinstance(bot,MCBot)
    help_lines=[
        f"接受指令前缀: - &{' /' if not is_mc else ''}",
        "help 显示本帮助",
        "sysinfo 显示运行此Bot的系统信息"
    ]
        
    plugins=get_loaded_plugins()
    for plugin in plugins:
        if hasattr(plugin.module,"get_help"):
            help_func=getattr(plugin.module,"get_help")
            if callable(help_func):
                try:
                    lines=help_func(bot,event)
                    if isinstance(lines,str):
                        help_lines.append(lines)
                    elif isinstance(lines,list):
                        help_lines.extend([str(l) for l in lines])
                except Exception as e:
                    logger.error(f"Error getting help from plugin {plugin.name}: {e}")
    
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
    description="显示帮助")
@slash.handle()
async def _(bot:Bot,event:Event):
    await slash.send(get_all_help(bot,event))

cmd = on_command("help")
@cmd.handle()
async def _(bot:Bot,event:Event):
    if(isinstance(bot,MCBot)):
        await cmd.send(get_all_help(bot,event))
    else:
        await cmd.send(get_all_help(bot,event))