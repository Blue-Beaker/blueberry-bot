from pathlib import Path
from typing import Any, TypeVar
from nonebot.adapters import Event,Bot
from nonebot.adapters.discord import GuildMessageCreateEvent,MessageEvent as DCMessageEvent,Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment,MessageEvent as OBMessageEvent
from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from . import sheets_api
sheets_api=sheets_api

def getid(event: Event) -> str:
    if isinstance(event,DCMessageEvent):
        return "dc_"+str(event.channel_id)
    if hasattr(event,"group_id"):
        return "group_"+str(getattr(event,"group_id"))
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
    
def supportsImage(bot:Bot):
    return isinstance(bot,OBBot) or isinstance(bot,DCBot)
    
class TextImageMessage:
    msg:DCMessage|OBMessage|str
    def __init__(self,msg:DCMessage|OBMessage|str) -> None:
        self.msg=msg
    @classmethod
    def build(cls,bot:Bot):
        if isinstance(bot,DCBot):
            return cls(DCMessage())
        elif isinstance(bot,OBBot):
            return cls(OBMessage())
        else:
            return cls("")
    def addText(self,text:str):
        self.msg+=text
        return self
    def addImage(self,image:bytes,image_name:str="image.png"):
        if isinstance(self.msg,DCMessage):
            self.msg.append(DCMessageSegment.attachment(image_name,content=image))
        elif isinstance(self.msg,OBMessage):
            self.msg.append(OBMessageSegment.image(image))
        return self