from pathlib import Path
import time
from typing import Any, TypeVar
import uuid
from nonebot.adapters import Event,Bot,Message
from nonebot.adapters.discord import GuildMessageCreateEvent,MessageEvent as DCMessageEvent,Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment,MessageEvent as OBMessageEvent
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment, MessageEvent as QQMessageEvent, C2CMessageCreateEvent as QQC2CMessageCreateEvent, GroupMessageCreateEvent as QQGroupMessageCreateEvent
from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from . import sheets_api
sheets_api=sheets_api
from nonebot import get_plugin_config,logger
from .config import Config
from .profile_link.profile_link import get_profile_link_manager

plugin_config=get_plugin_config(Config)

import re

def infer_id_prefix(raw_id: str) -> str:
    """根据 ID 形式推断平台前缀（与 get_raw_id 格式一致）。
    
    规则:
      - 不超过 10 位纯数字 → group_ (OneBot 群号)
      - 超过 10 位纯数字 → dc_ (Discord 频道/用户 ID)
      - 32 位大写十六进制 → qqgroup_ / qquser_ (QQ openid)
      - 其他 → mc_ (Minecraft 服务器名等)
    """
    if re.fullmatch(r"\d{1,10}", raw_id):
        return "group_"
    if re.fullmatch(r"\d+", raw_id):
        return "dc_"
    if re.fullmatch(r"[0-9A-F]{32}", raw_id):
        return "qqgroup_"
    return "mc_"

def get_raw_id(event: Event) -> str:
    """从事件中提取原始平台 ID（不含 profile_link 映射）。"""
    if isinstance(event,DCMessageEvent):
        return "dc_"+str(event.channel_id)
    if isinstance(event,MCBaseChatEvent):
        return "mc_"+event.server_name
    
    if isinstance(event,QQGroupMessageCreateEvent):
        return "qqgroup_"+event.group_id
    if isinstance(event,QQMessageEvent):
        return "qquser_"+event.get_user_id()
    if hasattr(event,"group_id"):
        return "group_"+str(getattr(event,"group_id"))
    
    return "u_" + str(event.get_user_id())

def get_raw_user_id(event: Event) -> str:
    """从事件中提取带平台前缀的用户 ID（用户级别，与 get_raw_id 格式一致）。"""
    raw_uid = event.get_user_id().replace(" ","_")
    
    if isinstance(event,DCMessageEvent):
        return f"dc_{raw_uid}"
    if isinstance(event,OBMessageEvent):
        return f"u_{raw_uid}"
    if isinstance(event,QQMessageEvent):
        return f"qquser_{raw_uid}"
    if isinstance(event,MCBaseChatEvent):
        return f"mc_{raw_uid}"
    return f"u_{raw_uid}"

def get_user_id(event: Event) -> str:
    raw_id = get_raw_user_id(event)
    # profile_link 解析：实际 ID → 通用 ID
    manager = get_profile_link_manager()
    resolved = manager.resolve_user_id(raw_id)
    return resolved
    

def getid(event: Event) -> str:
    raw_id = get_raw_id(event)
    # profile_link 解析：实际 ID → 通用 ID
    manager = get_profile_link_manager()
    resolved = manager.resolve_user_id(raw_id)
    return resolved

def is_group_event(event):
    """判断事件是否为群组/频道/服务器事件。"""
    if isinstance(event,DCMessageEvent):
        return True
    if isinstance(event,MCBaseChatEvent):
        return True
    if isinstance(event,QQGroupMessageCreateEvent):
        return True
    if hasattr(event,"group_id"):
        return True
    return False

def get_raw_group_id(event):
    """从事件中提取带平台前缀的原始群 ID（不含 profile_link 映射）。
    
    群组事件返回格式与 get_raw_id 一致，非群组事件返回 "private"。
    """
    if is_group_event(event):
        return get_raw_id(event)
    return "private"

def get_group_id(event):
    group_id = get_raw_group_id(event)
    
    # profile_link 解析：实际群 ID → 通用 ID
    if group_id != "private":
        manager = get_profile_link_manager()
        resolved = manager.resolve_group_id(group_id)
        if resolved:
            return resolved
    return group_id

    
async def reaction_emoji(bot:OBBot,msg:int,emoji:int):
    data={
    "message_id": msg,
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
    try:
        return int(i)
    except:
        return fallback
    
def supportsImage(bot:Bot):
    return isinstance(bot,OBBot) or isinstance(bot,DCBot) or isinstance(bot,QQBot)

def supportsMarkdown(bot:Bot):
    return isinstance(bot,DCBot)
    
class TextImageMessage:
    msg:DCMessage|OBMessage|QQMessage|str
    def __init__(self,msg:DCMessage|OBMessage|QQMessage|str) -> None:
        self.msg=msg
    @classmethod
    def build(cls,bot:Bot):
        if isinstance(bot,DCBot):
            return cls(DCMessage())
        elif isinstance(bot,OBBot):
            return cls(OBMessage())
        elif isinstance(bot,QQBot):
            return cls(QQMessage())
        else:
            return cls("")
    def addText(self,text:str):
        if isinstance(self.msg,Message):
            self.msg.append(text)
        else:
            self.msg+=text
        return self
    def addLine(self,text:str):
        if self.msg.__len__()>0 and (isinstance(self.msg,str) or self.msg[-1].is_text()):
            self.addText("\n")
        self.addText(text)
        return self
    def addImage(self,image:bytes,image_name:str="",small:bool=False):
        if isinstance(self.msg,DCMessage):
            if not image_name:
                image_name=uuid.uuid4().hex+".png"
            self.msg.append(DCMessageSegment.attachment(image_name,content=image))
        elif isinstance(self.msg,OBMessage):
            if small:
                imgsegment=OBMessageSegment.image(image)
                imgsegment.data["sub_type"]=1
                self.msg.append(imgsegment)
            else:
                self.msg.append(OBMessageSegment.image(image))
        elif isinstance(self.msg,QQMessage):
            self.msg.append(QQMessageSegment.file_image(image,image_name))
        return self
    def getMessage(self):
        return self.msg
    def getPlainText(self):
        if isinstance(self.msg,Message):
            return self.msg.extract_plain_text()
        else:
            return self.msg
    
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


# ── getid 指令 ────────────────────────────────────────

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

getid_cmd = on_command("getid")

@getid_cmd.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    manager = get_profile_link_manager()
    raw_id = get_raw_id(event)
    resolved_id = getid(event)
    group_id = get_group_id(event)
    raw_group = get_raw_group_id(event)
    user_id = get_raw_user_id(event)
    
    lines = [f"平台ID: {raw_id}", f"用户ID: {user_id}", f"群组ID: {raw_group}"]
    
    # 显示 profile_link 绑定信息
    profile = manager.find_user_by_linked_id(raw_id)
    if profile:
        lines.append(f"用户绑定到: {profile.name}")
        if profile.linked_ids:
            lines.append(f"  关联ID: {', '.join(profile.linked_ids)}")
            
    profile2 = manager.find_group_by_linked_id(raw_id)
    if profile2:
        lines.append(f"群组绑定到: {profile2.name}")
        if profile2.linked_ids:
            lines.append(f"  关联ID: {', '.join(profile2.linked_ids)}")
            
    if resolved_id != raw_id:
        lines.append(f"解析ID: {resolved_id}")
    
    # 群组绑定
    group_profile = manager.find_group_by_linked_id(raw_group) if raw_group != "private" else None
    if group_profile and group_profile.name != (profile.name if profile else None):
        lines.append(f"群绑定到: {group_profile.name}")
    
    # 处理 at 其他人
    at_users = []
    if isinstance(event, OBMessageEvent):
        for seg in event.get_message():
            if seg.type == "at" and str(seg.data.get("qq")) != bot.self_id:
                at_users.append(str(seg.data.get("qq")))
    elif isinstance(bot,DCBot) and isinstance(event, DCMessageEvent):
        for seg in event.get_message():
            if seg.type == "mention_user" and str(seg.data.get("user_id")) != bot.self_info.id:
                at_users.append(str(seg.data.get("user_id")))
    elif isinstance(bot,QQBot) and isinstance(event, QQMessageEvent):
        for seg in event.get_message():
            if seg.type == "mention_user":
                uid = str(seg.data.get("user_id", ""))
                if uid and uid != bot.self_info.id:
                    at_users.append(uid)
    
    if at_users:
        lines.append("")
        lines.append("被@用户:")
        for uid in at_users:
            # 尝试查找该用户的 profile_link
            uprofile = manager.find_user_by_linked_id(uid)
            if uprofile:
                lines.append(f"  {uid} → {uprofile.name}")
            else:
                lines.append(f"  {uid}")
    
    await getid_cmd.finish("\n".join(lines))