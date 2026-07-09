import traceback
from nonebot import logger, require,get_plugin_config,on_command
from nonebot.exception import IgnoredException,FinishedException
from nonebot.message import run_preprocessor,event_preprocessor
from nonebot.adapters import Bot,Event,Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from .config import Config

from nonebot.adapters.qq import Bot as QQBot,QQMessageEvent,C2CMessageCreateEvent,GroupAtMessageCreateEvent

plugin_config=get_plugin_config(Config)

require("bbot_api")
from ..bbot_api import getid,get_group_id,get_raw_id

debuglist=set(plugin_config.debug_sessions)

# @event_preprocessor
# async def _(bot:Bot, event: Event):
#     if isinstance(event,GroupAtMessageCreateEvent):
#         logger.info(f"{type(event)} {event.get_user_id()},{event.get_session_id()},{event.group_id},{event.group_openid}")
#     elif isinstance(event,C2CMessageCreateEvent):
#         logger.info(f"{type(event)} {event.get_user_id()},{event.get_session_id()}")
        
@run_preprocessor
async def _(event: Event, matcher: Matcher):
    if isinstance(matcher,debug_cmd):
        return
    if matcher.module_name and matcher.module_name.split(".")[-1] in plugin_config.debug_always_allowed_plugins:
        return
    # debuglist=plugin_config.debug_sessions
    try:
        eid = get_raw_id(event)
        is_listed=(eid in debuglist)
        
        if is_listed!=plugin_config.debug_sessions_is_on:
            # logger.info(f"Ignored {event} from {eid}")
            raise IgnoredException(f"Blocked: {eid}")
    except Exception as e:
        if isinstance(e,IgnoredException):
            raise e
        pass
    
debug_cmd=on_command("debug",permission=SUPERUSER)
@debug_cmd.handle()
async def _(bot:Bot, event: Event, msg: Message=CommandArg()):
    args=msg.extract_plain_text().strip().split()
    try:
        subcmds=["id","list","on","off"]
        
        if not args or args[0].lower()=="id":
            session_id=getid(event)
            group_id=get_group_id(event)
            
            is_listed=(session_id in debuglist)
            
            await debug_cmd.finish(f"当前 Debug {'on' if is_listed else 'off'}\nSession ID: {session_id}, Group ID:{group_id}")
            
            return
        
        subcmd=args[0].lower()
        if subcmd=="list":
            await debug_cmd.finish(f"当前调试Sessions: {','.join(debuglist)}")
            return
            
        elif subcmd in ["on","off"]:
            session_id=getid(event) if args.__len__()<2 else args[1]
            if subcmd=="on":
                debuglist.add(session_id)
                await debug_cmd.finish(f"已为 {session_id} 开启调试")
                return
            else:
                if session_id in debuglist: debuglist.remove(session_id)
                await debug_cmd.finish(f"已为 {session_id} 关闭调试")
                return
            
        await debug_cmd.finish(f"子命令: {",".join(subcmds)}")
    except Exception as e:
        if isinstance(e,FinishedException):
            raise e
        await debug_cmd.send(f"错误. 请检查日志")
        logger.error(f"Error executing debug command: {traceback.format_exc()}")
    