import math
import os
import random
import threading
import time
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
import nonebot.config
from nonebot import get_driver,require
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment

require('bbot_api')
from ..bbot_api.argparse import ArgumentError,ArgParser
require('gd_api')
from ..gd_api.gd import getLevel2,getList2,getUser
from ..gd_api import gd
from ..gd_api.thumbs import getThumbnail

driver=get_driver()

gdlist = on_command("gdlist")
@gdlist.handle()
async def _(args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 1
        
    except Exception as e:
        await gdlist.finish(str(e))
        return
    
    lines:list[str]=[]
    lists,pageinfo=getList2(search,page-1)
    
    if lists.__len__()==0 or not pageinfo:
        lines.append("没有查找到任何List.")
    elif lists.__len__()>1:
        lines.append(f"第 {page}/{math.ceil(pageinfo.total/pageinfo.amount)} 页 ({pageinfo.offset}-{pageinfo.offset+pageinfo.amount}/{pageinfo.total})")
        for l in lists:
            lines.append(f"{l.name} by {l.creator} ({l.id}) ({l.levels.__len__()} 个关卡)")
        await gdlist.finish("\n".join(lines))
        return
    l=lists[0]
    lines.append(f"{l.name} by {l.creator} ({l.id}) ({l.levels.__len__()} 个关卡)")
    await gdlist.finish("\n".join(lines))
    

gdthumb = on_command("gdthumb")
@gdthumb.handle()
async def _(bot:OBBot|DCBot,args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('-a',help='Include Unrated',action='store_true')
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 1
        rated=not parsed.a
        
    except Exception as e:
        await gdthumb.finish(str(e))
        return
    
    lines:list[str]=[]
    levels,pageinfo=getLevel2(search,page-1,rated)
    if not isinstance(levels,list):
        await gdthumb.finish("查找出错.")
        return
    if levels.__len__()==0:
        await gdthumb.finish("没有查找到任何关卡.")
        return
    elif levels.__len__()>1 and pageinfo:
        lines.append("找到多个关卡,请用id选择:")
        lines.append(f"第 {page}/{math.ceil(pageinfo.total/pageinfo.amount)} 页 ({pageinfo.offset}-{pageinfo.offset+pageinfo.amount}/{pageinfo.total})")
        for l in levels:
            lines.append(f"{l.id} = {l.name} by {l.creator} ({l.repr_difficulty()})")
        await gdthumb.finish("\n".join(lines))
        return
    
    l=levels[0]
    thumb=getThumbnail(l.id)
    if not thumb:
        await gdthumb.finish(f"未找到该关卡截图: {l.name} by {l.creator} ({l.repr_difficulty()})")
        return
    else:
        await gdthumb.finish(buildMessageImage(bot,f"{l.name} by {l.creator} ({l.repr_difficulty()})",thumb,f"{l.id}.png"))
        return
    
gduser = on_command("gduser")
@gduser.handle()
async def _(args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('-c',help='Show Classic breakdown',action='store_true')
        parser.add_argument('-p',help='Show Platformer breakdown',action='store_true')
        parser.add_argument('-d',help='Show Demons breakdown',action='store_true')
        parser.add_argument('-v',help='Show Other Info',action='store_true')
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        search=" ".join(parsed.search)
        show_classic=bool(parsed.c)
        show_plat=bool(parsed.p)
        show_demons=bool(parsed.d)
        show_other=bool(parsed.v)
        
    except Exception as e:
        await gduser.finish(str(e))
        return
    
    lines:list[str]=[]
    
    user=getUser(search)
    if not user:
        await gduser.finish("未找到玩家, 或发生错误.")
        
    lines.append(f"{user.user_name}")
    stats_line=f"{user.stars}★ {user.moons}🌙 {user.secret_coins}✪ {user.user_coins}© {user.demons}😈 {user.diamonds}💎"
    if user.creator_points:
        stats_line+=f"{user.creator_points}🛠"
    lines.append(stats_line)
    
    c=user.classic_levels
    p=user.plat_levels
    demons=user.classic_demons
    pemons=user.plat_demons
    
    def format_nondemons(l:gd.PlayerLevels):
        return f"{l.auto}🤖 {l.easy}😃 {l.normal}🙂 {l.hard}🙁, {l.harder}😡, {l.insane}😫"
    
    lines.append(f"Non-demons: {user.classic_levels.sum()}, Non-pemons: {user.plat_levels.sum()}")
    lines.append(f"Demons: {demons.sum()}, Pemons: {pemons.sum()}")
    
    
    if not (show_classic or show_plat or show_demons):
        lines.append("使用-c、-p、-d参数, 可显示Classic、Plat与Demon关卡的详细计数")
    
    if show_classic:
        lines.append(f"Classic: ")
        lines.append(format_nondemons(user.classic_levels))
        lines.append(f"Daily: {c.daily} Gauntlets: {c.gauntlet}")
        
    if show_plat:
        lines.append(f"Plat: ")
        lines.append(format_nondemons(user.plat_levels))
    
    if show_demons:
        lines.append(f"{demons.ezd}EZD {demons.med}MED {demons.hdd}HDD {demons.insd}INSD {demons.exd}EXD")
        lines.append(f"{pemons.ezd}EZP {pemons.med}MEP {pemons.hdd}HDP {pemons.insd}INSP {pemons.exd}EXP")
        lines.append(f"Weekly: {demons.weekly} Gauntlets: {demons.gauntlet}")
        
    if show_other:
        lines.append(f"Global Rank {user.global_rank}")
        lines.append(f"Account ID {user.account_id}")
        lines.append(f"Player ID {user.user_id}")
    
    await gduser.finish("\n".join(lines))
    
    
def buildMessageImage(bot:Bot,message:str,image:bytes,image_name:str):
    if isinstance(bot,OBBot):
        return(OBMessageSegment.text(message)+OBMessageSegment.image(image))
    else:
        return(DCMessage().append(message).append(DCMessageSegment.attachment(image_name,content=image)))
    

def get_help(bot:Bot,event:Event):
    if isinstance(bot,OBBot) or isinstance(bot,DCBot):
        return ["gdthumb [关名/ID] 获取关卡截图",
                "gduser [用户名/ID] 展示玩家信息"]
    else:
        return None