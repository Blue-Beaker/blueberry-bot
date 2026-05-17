from pathlib import Path
from typing import Any, TypeVar
from nonebot.adapters import Event
from nonebot.adapters.discord import GuildMessageCreateEvent,MessageEvent as DCMessageEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot
from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from . import sheets_api
sheets_api=sheets_api

def getid(event: Event) -> str:
    if isinstance(event,DCMessageEvent):
        return "dc_"+str(event.channel_id)
    if isinstance(event,OBGroupMessageEvent):
        return "group_"+str(event.group_id)
    if isinstance(event,MCBaseChatEvent):
        return "mc_"+event.server_name
    else:
        return "u_" + str(event.get_user_id())
    
async def reaction_emoji(bot:OBBot,msg:int,emoji:int):
    data={
    "message_id": msg,
    "emoji_id": str(emoji),
    "set": True
    }
    await bot.call_api("set_msg_emoji_like",**data)
    
def loadFile(file:str|Path) -> bytes:
    with open(file,'rb') as f:
        return f.read()
    
_A = TypeVar(name="_A")
def safeInt(i:Any,fallback:_A=-1) -> int|_A:
    try:
        return int(i)
    except:
        return fallback