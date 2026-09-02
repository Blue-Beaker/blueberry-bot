from nonebot.adapters import Event,Bot,Message
from nonebot.adapters.discord import MessageEvent as DCMessageEvent,Bot as DCBot
from nonebot.adapters.onebot.v11 import MessageEvent as OBMessageEvent
from nonebot.adapters.qq import Bot as QQBot, MessageEvent as QQMessageEvent
from . import sheets_api
sheets_api=sheets_api
from .profile_link.profile_link import get_profile_link_manager
from .id_resolve import get_raw_id,get_raw_user_id,get_group_id,get_profile_link_manager,get_raw_group_id,getid

# ── getid 指令 ────────────────────────────────────────

from nonebot import on_command
from nonebot.params import CommandArg

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
    
    # 用户绑定 — 用 user_id（用户级）查找
    user_profile = manager.find_user_by_linked_id(user_id)
    if user_profile:
        lines.append(f"用户绑定到: {user_profile.profile_label}")
        if user_profile.linked_ids:
            lines.append(f"  关联ID: {', '.join(user_profile.linked_ids)}")
    
    # 群组绑定 — 用 raw_group（群级）查找
    group_profile = manager.find_group_by_linked_id(raw_group) if raw_group != "private" else None
    if group_profile:
        lines.append(f"群组绑定到: {group_profile.profile_label}")
        if group_profile.linked_ids:
            lines.append(f"  关联群ID: {', '.join(group_profile.linked_ids)}")
            
    if resolved_id != raw_id:
        lines.append(f"解析ID: {resolved_id}")
    
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
                lines.append(f"  {uid} -> {uprofile.profile_label}")
            else:
                lines.append(f"  {uid}")
    
    await getid_cmd.finish("\n".join(lines))