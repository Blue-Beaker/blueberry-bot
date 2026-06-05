import datetime
from pathlib import Path
import random
import time
from typing import Any
from nonebot import get_plugin_config,logger,on_command,on_message,on_notice,on_type,require,get_driver
from nonebot.adapters import Bot,Event
from nonebot.adapters.onebot.v11 import Bot as OBBot, MessageEvent as OBMessageEvent, GroupMessageEvent, PokeNotifyEvent
from nonebot.adapters.onebot.v11.message import Message,MessageSegment
from nonebot.message import run_postprocessor
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

from .config import Config

require("bbot_api")
from ..bbot_api.group_config import GroupConfig, ConfigItem, make_config_handler

plugin_config = get_plugin_config(Config)

class OBInteractionConfigItem(ConfigItem):
    group_sign_chance: float=0.01
    msg_poke_chance: float=0.0
    cmd_like_chance: float=0.01
    cmd_poke_chance: float=0.1
    
CONFIG_FILE_PATH=Path("config/ob_interaction.json")
CONFIG_FILE_PATH.parent.mkdir(parents=True,exist_ok=True)

PRIVATE_SESSION_KEY="private"

group_config = GroupConfig(OBInteractionConfigItem,CONFIG_FILE_PATH.__str__())

driver=get_driver()

@driver.on_startup
async def _():
    group_config.load()
    
@driver.on_shutdown
async def _():
    group_config.save()

        
onMsg=on_message()
@onMsg.handle()
async def _(bot:OBBot,event:OBMessageEvent):
    text=event.message.extract_plain_text().strip()
    if text.__len__()<5 or text[0] not in get_driver().config.command_start:
        if isinstance(event,GroupMessageEvent) and random.random()<group_config.get(str(event.group_id)).msg_poke_chance:
            await bot.call_api("group_poke",group_id=event.group_id,user_id=event.user_id)
        return
    
    group_id = getattr(event,"group_id",None)
    user_id = getattr(event,"user_id",None)
    
    if not user_id:
        return
    
    if group_id:
        like_chance=group_config.get(str(group_id)).cmd_like_chance
        poke_chance=group_config.get(str(group_id)).cmd_poke_chance
    else:
        like_chance=group_config.get(PRIVATE_SESSION_KEY).cmd_like_chance
        poke_chance=group_config.get(PRIVATE_SESSION_KEY).cmd_poke_chance
        
    if random.random()<like_chance:
        await try_like(bot,user_id)
        
    if group_id and random.random()<poke_chance:
        await bot.call_api("group_poke",group_id=group_id,user_id=user_id)
    
    if group_id and random.random()<get_group_sign_chance(group_id):
        try:
            await bot.call_api("send_group_sign",group_id=group_id)
        except:
            pass
        
        
onPoke=on_type(PokeNotifyEvent)
@onPoke.handle()
async def _(bot: OBBot, event:PokeNotifyEvent):
    logger.info(event)
    if event.is_tome() and random.random()<plugin_config.ob_poke_back_chance:
        if event.group_id:
            await bot.call_api("group_poke",group_id=event.group_id,user_id=event.user_id)
        else:
            await bot.call_api("friend_poke",user_id=event.user_id)
            
# 注册可复用的配置指令
from nonebot.permission import SUPERUSER
from nonebot import on_command

config_matcher = on_command("interaction_config", permission=SUPERUSER)
config_handler = make_config_handler("interaction_config", OBInteractionConfigItem, group_config)
config_matcher.handle()(config_handler)

def get_group_sign_chance(group_id:int):
    return group_config.get(str(group_id)).group_sign_chance

async def try_like(bot:OBBot, user_id:int):
    try:
        await bot.send_like(user_id=user_id,times=10)
    except:
        pass