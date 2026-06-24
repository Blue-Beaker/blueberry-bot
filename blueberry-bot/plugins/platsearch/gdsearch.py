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
from .plat_sheets import LevelEntry,TheListsEntry,PlatChartEntry
from .data_cache import ManagedIDMapCache
from . import formatters

require('bbot_api')
from .. import bbot_api
from ..bbot_api.argparse import ArgumentError,ArgParser
require('gd_api')
from ..gd_api.gd import getLevel2,getList2,getUser,getLevelsFromList,ListSearchType,LevelSearchType,PlayerIcons
from ..gd_api import gd
from ..gd_api.thumbs import getThumbnail

driver=get_driver()
plugin_cfg=get_plugin_config(Config)

render_api=godot_draw.RenderAPI()
render_api.uri=plugin_cfg.render_server_uri

PLAT_CHART_BY_ID=ManagedIDMapCache(PLAT_CHART_CACHE)
PLAT_SHEET_BY_ID=ManagedIDMapCache(PLAT_SHEET_CACHE)

gdsearch = on_command("gdsearch")
@gdsearch.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('--classic',help='Classic only',action='store_true')
        parser.add_argument('--plat',help='Classic only',action='store_true')
        parser.add_argument('-d',help='Demon Difficulty',type=str,default=None)
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
        demon=bool(parsed.d)
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
        await gdsearch.finish(lines.msg)
        return
    
    level=levels[0]
        
    supports_image=(isinstance(bot,OBBot) or isinstance(bot,DCBot))
    enable_image=(not force_text) and supports_image
    
    info_image=False
    
    # Image Sections
    # if enable_image:
    #     req_id_base=bbot_api.getid(event)
    #     user_info_args:dict[str,str]={}
        
    #     player_icons=getIconIDs(user.icon)
    #     icon_type=ICON_TYPES[icon.icon_type]
        
    #     user_info_args["player_icon"]=construct_icon_url(icon_type,player_icons.get(icon_type,0),icon.color,icon.color2,icon.glow_color)
        
    #     if show_thumbnail:
    #         for i,id in player_icons.items():
    #             user_info_args["icon_"+i.value]=construct_icon_url(i,id,icon.color,icon.color2,icon.glow_color)
        
    #     img=await render_api.render_player_info(req_id_base+"_base",user.user_name,user.stars,user.moons,user.secret_coins,user.user_coins,user.demons,user.creator_points,c.sum(),p.sum(),c_demons.sum(),pemons.sum(),**user_info_args)
    #     if isinstance(img,bytes):
    #         msg.addImage(img)
    #         info_image=True
            
    # Basic Info (Text)
    if not info_image:
        lines.addLine(repr_level(level))
        
        if level.is_plat():
            
            dc_entries=PLAT_CHART_BY_ID.get_for_id(level.id)
            for e in dc_entries:
                lines.addLine(formatters.formatDiffChart(e,False,True))
            
            lists_entries=PLAT_SHEET_BY_ID.get_for_id(level.id)
            for e in lists_entries:
                lines.addLine(formatters.formatListsLevel(e,False,True))
            
            
        
    
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
        
    await gdsearch.finish(lines.msg)

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