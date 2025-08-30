import json
import traceback
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot
from nonebot.adapters.minecraft import BaseChatEvent,MessageEvent
from nonebot.adapters.discord.bot import Bot as DCBot
from nonebot.adapters.discord import Adapter as DCAdapter
from nonebot.adapters.discord.api import Snowflake
from nonebot.adapters import Message
from nonebot.params import CommandArg

from config import Config

plugin_config = get_plugin_config(Config)

handler_msg = on_type(BaseChatEvent)
@handler_msg.handle()
async def _(bot:Bot,event:BaseChatEvent):
    targetid=plugin_config.mc_sync_mappings.get(event.server_name,None)
    # logger.info(event.server_name,plugin_config.mc_sync_mappings)
    if not targetid:
        return
    
    sender=event.player.nickname
    messageStr=event.message
    sendMessage=f"[{sender}]: {messageStr}"
    # logger.info(f"Message in {event.server_name} [{sender}]: {messageStr}")
    
    dcadapter = get_adapter(DCAdapter)
    if not dcadapter:
        logger.info("Discord adapter not present")
        return
    for name,dcbot in dcadapter.bots.items():
        assert isinstance(dcbot,DCBot)
        logger.info(f"Sending on dcbot {dcbot}")
        await dcbot.send_to(channel_id=Snowflake(targetid),message=sendMessage)
