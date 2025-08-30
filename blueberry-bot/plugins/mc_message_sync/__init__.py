import json
import traceback
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot
from nonebot.adapters.minecraft import BaseChatEvent,MessageEvent,NoticeEvent,BaseJoinEvent,BaseQuitEvent
from nonebot.adapters.discord.bot import Bot as DCBot
from nonebot.adapters.discord import Adapter as DCAdapter
from nonebot.adapters.discord.api import Snowflake
from nonebot.adapters import Message
from nonebot.params import CommandArg
import nonebot.config

from config import Config

plugin_config = get_plugin_config(Config)

async def sendMessageToDiscord(targetid:int, sendMessage:str):
    dcadapter = get_adapter(DCAdapter)
    if not dcadapter:
        logger.info("Discord adapter not present")
        return
    for name,dcbot in dcadapter.bots.items():
        assert isinstance(dcbot,DCBot)
        logger.info(f"Sending on dcbot {dcbot}")
        await dcbot.send_to(channel_id=Snowflake(targetid),message=sendMessage)

handler_msg = on_type(BaseChatEvent)
@handler_msg.handle()
async def _(bot:Bot,event:BaseChatEvent):
    targetid=plugin_config.mc_sync_mappings.get(event.server_name,None)
    # logger.info(event.server_name,plugin_config.mc_sync_mappings)
    if not targetid:
        return
    
    sender=event.player.nickname
    messageStr=event.message
    
    stripped=str(messageStr).strip()
    # 不对bot指令进行转发
    
    for start in get_plugin_config(nonebot.config.Config).command_start:
        if(stripped.startswith(start)):
            return
    
    sendMessage=f"[{sender}]: {messageStr}"
    await sendMessageToDiscord(targetid, sendMessage)
    # logger.info(f"Message in {event.server_name} [{sender}]: {messageStr}")
    

handler_notice = on_type(NoticeEvent)
@handler_notice.handle()
async def _(bot:Bot,event:NoticeEvent):
    if not plugin_config.mc_sync_notice_events:
        return
    targetid=plugin_config.mc_sync_mappings.get(event.server_name,None)
    if not targetid:
        return
    if isinstance(event,BaseJoinEvent):
        await sendMessageToDiscord(targetid, f"{event.player} joined the server")
    elif isinstance(event,BaseQuitEvent):
        await sendMessageToDiscord(targetid, f"{event.player} left the server")