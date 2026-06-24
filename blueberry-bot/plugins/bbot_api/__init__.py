from pathlib import Path
import time
from typing import Any, TypeVar
from nonebot.adapters import Event,Bot,Message
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
    def addLine(self,text:str):
        if self.msg.__len__()>0 and (isinstance(self.msg,str) or self.msg[-1].is_text()):
            self.addText("\n")
        self.addText(text)
        return self
    def addImage(self,image:bytes,image_name:str="image.png",small:bool=False):
        if isinstance(self.msg,DCMessage):
            self.msg.append(DCMessageSegment.attachment(image_name,content=image))
        elif isinstance(self.msg,OBMessage):
            if small:
                imgsegment=OBMessageSegment.image(image)
                imgsegment.data["sub_type"]=1
                self.msg.append(imgsegment)
            else:
                self.msg.append(OBMessageSegment.image(image))
        return self
    def getMessage(self):
        return self.msg
    def getPlainText(self):
        if isinstance(self.msg,Message):
            return self.msg.extract_plain_text()
        else:
            return self.msg
    
def get_group_id(event):
    print(event)
    if isinstance(event,MCBaseChatEvent):
        group_id=event.server_name
    else:
        for field in ["group_id","channel_id"]:
            group_id=getattr(event,field,None)
            if group_id:
                break
        
    if group_id:
        group_id=str(group_id)
    else:
        group_id="private"
    print(group_id)
    return group_id

def can_pack_message(bot:Bot):
    return isinstance(bot,OBBot)

class LoginInfo:
    user_id:int=-1
    nickname:str=""
    expiration:int=0
    
    async def update(self,bot:OBBot):
        if self.user_id>0 and self.nickname and time.time()<self.expiration:
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