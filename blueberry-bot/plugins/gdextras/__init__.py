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
from ..gd_api.gd import getLevel,getList
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
        page=parsed.p or 0
        
    except Exception as e:
        await gdlist.finish(str(e))
        return
    
    lines:list[str]=[]
    lists=getList(search,page)
    
    if lists.__len__()==0:
        lines.append("没有查找到任何List.")
    else:
        for l in lists:
            lines.append(f"{l.id} = {l.name} by {l.creator}")
    await gdlist.finish("\n".join(lines))
    

gdthumb = on_command("gdthumb")
@gdthumb.handle()
async def _(bot:Bot,args: Message = CommandArg()):
    
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('-a',help='Include Unrated',action='store_true')
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 0
        rated=not parsed.a
        
    except Exception as e:
        await gdthumb.finish(str(e))
        return
    
    lines:list[str]=[]
    levels=getLevel(search,page,rated)
    if not isinstance(levels,list):
        await gdthumb.finish("查找出错,可能是网络错误.")
        return
    if levels.__len__()==0:
        await gdthumb.finish("没有查找到任何关卡.")
        return
    elif levels.__len__()>1:
        lines.append("找到多个关卡,请用id选择:")
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
    
    
    
def buildMessageImage(bot:Bot,message:str,image:bytes,image_name:str):
    if isinstance(bot,OBBot):
        return(OBMessageSegment.text(message)+OBMessageSegment.image(image))
    else:
        return(DCMessage().append(message).append(DCMessageSegment.attachment(image_name,content=image)))