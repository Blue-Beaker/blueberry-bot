import math
import os
import random
import threading
import traceback
import time
from typing import Any, Generic, Sequence, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.exception import FinishedException
import nonebot.config
from nonebot import get_driver,require
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment

from . import godot_draw
from .config import Config
from .gd_icon import IconType, construct_icon_url,get_icon,ICON_TYPES
from .gd_extras import repr_level
from .platsearch import PLAT_CHART_CACHE,PLAT_SHEET_CACHE
from .underrated import UR_CACHE,formatUnderrated
from .plat_sheets import LevelEntry,TheListsEntry,PlatChartEntry
from .data_cache import ManagedIDMapCache
from . import formatters

require('bbot_api')
from .. import bbot_api
from ..bbot_api.argparse import ArgumentError,ArgParser
require('gd_api')
from ..gd_api.gd import getLevel2,getList2,getUser,getLevelsFromList,ListSearchType,LevelSearchType,PlayerIcons
from ..gd_api import gd
from ..gd_api.thumbs import getThumbnail,getThumbnailUrl

driver=get_driver()
plugin_cfg=get_plugin_config(Config)

render_api=godot_draw.RenderAPI()
render_api.uri=plugin_cfg.render_server_uri

PLAT_CHART_BY_ID=ManagedIDMapCache(PLAT_CHART_CACHE)
PLAT_SHEET_BY_ID=ManagedIDMapCache(PLAT_SHEET_CACHE)
UNDERRATED_BY_ID=ManagedIDMapCache(UR_CACHE)

gdsearch = on_command("gdsearch")
@gdsearch.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('--classic',help='Classic only',action='store_true')
        parser.add_argument('--plat',help='Classic only',action='store_true')
        parser.add_argument('-d',help='Demon Difficulty',type=str,default="")
        parser.add_argument('-v',help='Show Other Info',action='store_true')
        parser.add_argument('-t',help='Plain Text',action='store_true')
        parser.add_argument('-i',help='Show Thumbnail',action='store_true')
        parser.add_argument('-a',help='Include Unrated',action='store_true')
        parser.add_argument('-p',help='Page',type=int,default=0)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        search=" ".join(parsed.search)
        classic_only=bool(parsed.classic)
        plat_only=bool(parsed.plat)
        demon=str(parsed.d)
        show_other=bool(parsed.v)
        force_text=bool(parsed.t)
        show_thumbnail=bool(parsed.i)
        include_unrated=bool(parsed.a)
        page=int(parsed.p)
        
    except Exception as e:
        await gdsearch.finish(str(e))
        return
    
    lines=bbot_api.TextImageMessage.build(bot)
    
    kwargs={}
    if classic_only:
        kwargs["len"]="0,1,2,3,4"
    if plat_only:
        kwargs["len"]="5"
    if demon:
        kwargs["diff"]=-2
        if demon.lower()!='all':
            kwargs["demonFilter"]=demon
            
    print(demon,kwargs)
    
    levels,pageinfo=getLevel2(search,page=page,rated=not include_unrated,**kwargs)
    if not isinstance(levels,list):
        await gdsearch.finish("查找出错.")
        return
    if levels.__len__()==0:
        await gdsearch.finish("没有查找到任何关卡.")
        return
    elif levels.__len__()>1 and pageinfo:
        lines.addLine("找到多个关卡,请用id选择:")
        lines.addLine(f"第 {page}/{math.ceil(pageinfo.total/pageinfo.amount)} 页 ({pageinfo.offset}-{pageinfo.offset+pageinfo.amount}/{pageinfo.total})")
        for l in levels:
            lines.addLine(repr_level(l))
            if l.is_plat():
                lines.addText("".join([f" E{l2.enj or '-'} W{l2.weight or '-'} P{l2.pemon or '-'}" for l2 in PLAT_CHART_BY_ID.get_for_id(l.id)]))
            
        await gdsearch.finish(await bbot_api.auto_pack_message(bot,lines.msg,6))
        return
    
    level=levels[0]
        
    supports_image=(isinstance(bot,OBBot) or isinstance(bot,DCBot))
    enable_image=(not force_text) and supports_image
    
    info_image=False
    
    dc_entry=None
    dc_entries=PLAT_CHART_BY_ID.get_for_id(level.id)
    if dc_entries:
        dc_entry=dc_entries[0]
        
    lists_entries=PLAT_SHEET_BY_ID.get_for_id(level.id)
    
    # Image Sections
    if enable_image:
        req_id_base=bbot_api.getid(event)
        extra_render_args:dict[str,Any]={}
        if dc_entry:
            extra_render_args.update({
                "weight":str(dc_entry.weight or '-'),
                "pemonlist":str(dc_entry.pemon or '-'),
                "diffchart_tier":dc_entry.tier or '',
            })
        if lists_entries:
            for l in lists_entries:
                if l.checkpoints: extra_render_args["checkpoints"]=l.checkpoints.replace("∞","Infinite")
                break
        
        song=gd.getSong(level.songID)
        
        img=await render_api.render_level(req_id_base+"_base",
                        level_id=level.id,
                        level_name=level.name,
                        song_id=level.songID,
                        song_author=song.artistName if song else "Unknown",
                        song_name=song.name if song else "Unknown",
                        creator=level.creator,
                        stars=level.stars,
                        length=gd.Length(level.length).name,
                        difficulty=level.get_difficulty().value,
                        feature_level=level.epic+1 if level.featured>0 else 0,
                        is_plat=level.is_plat(),
                        coins=level.coins,
                        downloads=level.downloads,
                        scene_type="level_large",
                        thumbnail=getThumbnailUrl(level.id),
                        **extra_render_args
                        )
        if isinstance(img,bytes):
            msg2=bbot_api.TextImageMessage.build(bot)
            msg2.addLine(repr_level(level))
            msg2.addImage(img)
            info_image=True
            await gdsearch.send(msg2.msg)
            
    # Basic Info (Text)
    if not info_image:
        lines.addLine(repr_level(level))
    
    if level.is_plat():
        
        if dc_entries:
            lines.addLine("--Difficulty Chart--")
        for e in dc_entries:
            lines.addLine(formatters.formatDiffChart(e,False,True))
        
        if lists_entries:
            lines.addLine("--NLW/IDS/HDS--")
        for e in lists_entries:
            lines.addLine(formatters.formatListsLevel(e,False,True))
            
        ur_entries=UNDERRATED_BY_ID.get_for_id(level.id)
        if ur_entries:
            lines.addLine("--Underrated Levels--")
        for e in ur_entries:
            lines.addLine(formatUnderrated(e,False,True))
            
            
        
    
    # if not (classic_only or plat_only or demon):
    #     lines.append("使用-c、-p、-d参数, 可显示Classic、Plat与Demon关卡的详细计数")

    if show_thumbnail and supports_image:
        thumb=getThumbnail(level.id)
        if thumb:
            lines.addImage(thumb)
            
    # Others (Text)
    if show_other:
        pass
        # lines.append(f"Global Rank {user.global_rank}")
        # lines.append(f"Account ID {user.account_id}")
        # lines.append(f"Player ID {user.user_id}")
    if lines.msg.__len__():
        await gdsearch.finish(await bbot_api.auto_pack_message(bot,lines.msg,6))

def getIconIDs(icon: PlayerIcons):
    id_for_types:dict[IconType,int]={}
    for i in IconType:
        id_for_types[i]=icon.get_icon_for_type(i.value) or 0
    return id_for_types
    
async def render_nondemons(req_id:str,classic:gd.PlayerLevels,plat:gd.PlayerLevels):
    return await render_api.render_nondemons(req_id,classic.auto,classic.easy,classic.normal,classic.hard,classic.harder,classic.insane,classic.sum(),plat.auto,plat.easy,plat.normal,plat.hard,plat.harder,plat.insane,plat.sum(),classic.daily,classic.gauntlet)

async def render_demons(req_id:str,classic:gd.PlayerDemonLevels,plat:gd.PlayerDemonLevels):
    return await render_api.render_demons(req_id,classic.ezd,classic.med,classic.hdd,classic.insd,classic.exd,classic.sum(),plat.ezd,plat.med,plat.hdd,plat.insd,plat.exd,plat.sum(),classic.weekly,classic.gauntlet)

def get_help(bot:Bot,event:Event):
    return ["gdsearch [参数] [关名/ID] 搜索关卡"]