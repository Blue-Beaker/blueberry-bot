from pathlib import Path
import time
from typing import Any, Callable, Type, TypeVar
import uuid
from nonebot.adapters import Event,Bot,Message
from nonebot.adapters.discord import GuildMessageCreateEvent,MessageEvent as DCMessageEvent,Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment,MessageEvent as OBMessageEvent
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment, MessageEvent as QQMessageEvent, C2CMessageCreateEvent as QQC2CMessageCreateEvent, GroupMessageCreateEvent as QQGroupMessageCreateEvent
from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from . import sheets_api
_=sheets_api
from nonebot import get_plugin_config,logger
from .config import Config
from .profile_link.profile_link import get_profile_link_manager
from .message_compat import TextImageMessage,supportsRecord,supportsImage,supportsMarkdown
from .emoji_def import UNICODE_EMOJIS,QQ_EMOJIS

plugin_config=get_plugin_config(Config)

import re
from .id_resolve import infer_id_prefix,get_raw_id,get_raw_user_id,get_group_id,get_profile_link_manager,is_group_event,get_raw_group_id,getid,get_user_id

from . import getid_cmd

async def reaction_emoji(bot:Bot,event:Event,emoji:str,qq_alt_id:int|None=None):
    emoji_id=qq_alt_id
    if not qq_alt_id and (isinstance(bot,OBBot) or isinstance(bot,QQBot)):
        emoji_id=UNICODE_EMOJIS.get(emoji)
        if not emoji_id:
            raise ValueError(f"{emoji} not found for QQ")
    if emoji_id and isinstance(bot,OBBot) and isinstance(event,OBMessageEvent):
        await reaction_emoji_ob(bot,event,emoji_id)
    # elif emoji_id and isinstance(bot,QQBot) and isinstance(event,QQGroupMessageCreateEvent):
    #     await reaction_emoji_qq(bot,event,emoji_id)
    elif isinstance(bot,DCBot) and isinstance(event,DCMessageEvent):
        await reaction_emoji_dc(bot,event,emoji)
        
        
    
async def reaction_emoji_qq(bot:QQBot,event:QQGroupMessageCreateEvent,emoji:int):
    await bot.put_message_reaction(channel_id=event.group_openid,message_id=event.id,type=2 if emoji>9000 else 1,id=str(emoji))
    
async def reaction_emoji_ob(bot:OBBot,event:OBMessageEvent,emoji:int):
    data={
    "message_id": event.message_id,
    "emoji_id": str(emoji),
    "set": True
    }
    await bot.call_api("set_msg_emoji_like",**data)
    
async def reaction_emoji_dc(bot:DCBot,event:DCMessageEvent,emoji:str):
    await bot.create_reaction(channel_id=event.channel_id,message_id=event.message_id,emoji=emoji)
    
async def trigger_typing(bot:Bot,event:Event):
    if isinstance(bot,DCBot) and isinstance(event,DCMessageEvent):
        await bot.trigger_typing_indicator(channel_id=event.channel_id)
    
def loadFile(file:str|Path) -> bytes:
    with open(file,'rb') as f:
        return f.read()
    
_A = TypeVar(name="_A")
def safeInt(i:Any,fallback:_A=-1) -> int|_A:
    return safeConversion(i,int,-1)
    
def safeFloat(i:Any,fallback:_A=-1.0) -> float|_A:
    return safeConversion(i,float,-1.0)
    
_T = TypeVar(name="_T")
def safeConversion(i:Any, converter:Callable[[Any],_T],fallback:_A=None) -> _T|_A:
    try:
        return converter(i)
    except:
        return fallback
    
def can_pack_message(bot:Bot):
    return isinstance(bot,OBBot) and plugin_config.ob_pack_message

class LoginInfo:
    user_id:int=-1
    nickname:str=""
    expiration:int=0
    
    async def update(self,bot:OBBot):
        if self.user_id>0 and self.nickname and time.time()<self.expiration:
            return
        
        if plugin_config.ob_user_id:
            self.user_id=plugin_config.ob_user_id
        if plugin_config.ob_user_nickname:
            self.nickname=plugin_config.ob_user_nickname
        
        if plugin_config.ob_user_id and plugin_config.ob_user_nickname:
            self.expiration=int(time.time()+600)
            return
        login_info = await bot.get_login_info()
        self.user_id=login_info.get("user_id",-1)
        self.nickname=login_info.get("nickname","")
        self.expiration=int(time.time()+600)
        
_LOGIN_INFO=LoginInfo()

async def pack_message(bot:Bot,message:Any):
    if isinstance(bot,OBBot):
        await _LOGIN_INFO.update(bot)
    return OBMessageSegment.node_custom(_LOGIN_INFO.user_id,_LOGIN_INFO.nickname,message)

async def auto_pack_message(bot:Bot,message:Message|str,limit:int):
    if isinstance(message,Message): lines=message.extract_plain_text()
    else: lines=message
    if(lines.split("\n").__len__()>limit and can_pack_message(bot)):
        reply=await pack_message(bot,message)
        assert reply
        return reply
    return message
