from nonebot.adapters import Event
from nonebot.adapters.discord import MessageEvent as DCMessageEvent
from nonebot.adapters.onebot.v11 import MessageEvent as OBMessageEvent
from nonebot.adapters.qq import MessageEvent as QQMessageEvent, GroupMessageCreateEvent as QQGroupMessageCreateEvent
from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from . import sheets_api
sheets_api=sheets_api
from nonebot import get_plugin_config
from .config import Config
from .profile_link.profile_link import get_profile_link_manager

plugin_config=get_plugin_config(Config)

import re

def infer_id_prefix(raw_id: str) -> str:
    """根据 ID 形式推断平台前缀（与 get_raw_id 格式一致）。
    
    规则:
      - 不超过 10 位纯数字 -> group_ (OneBot 群号)
      - 超过 10 位纯数字 -> dc_ (Discord 频道/用户 ID)
      - 32 位大写十六进制 -> qqgroup_ / qquser_ (QQ openid)
      - 其他 -> mc_ (Minecraft 服务器名等)
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
    # profile_link 解析：实际 ID -> 通用 ID
    manager = get_profile_link_manager()
    resolved = manager.resolve_user_id(raw_id)
    return resolved
    

def getid(event: Event) -> str:
    raw_id = get_raw_id(event)
    # profile_link 解析：实际 ID -> 通用 ID
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
    # logger.info(group_id)
    
    # profile_link 解析：实际群 ID -> 通用 ID
    if group_id != "private":
        manager = get_profile_link_manager()
        resolved = manager.resolve_group_id(group_id)
        if resolved:
            group_id=resolved
            
    # logger.info(group_id)
    return group_id