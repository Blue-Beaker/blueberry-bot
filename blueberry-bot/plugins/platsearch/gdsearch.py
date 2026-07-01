from argparse import Namespace
from enum import Enum
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
from ..gd_api.gd import getLevel2,getLevelSearch2,getList2,getUser,getLevelsFromList,ListSearchType,LevelSearchType,PlayerIcons,downloadLevel2,LevelSearchArgs,Difficulty,Length,getLevelsFromUser,PageInfo
from ..gd_api import gd
from ..gd_api.thumbs import getThumbnail,getThumbnailUrl

driver=get_driver()
plugin_cfg=get_plugin_config(Config)

require('bbot_render')
from ..bbot_render import RenderAPI
render_api=RenderAPI()
render_api.uri=plugin_cfg.render_server_uri

PLAT_CHART_BY_ID=ManagedIDMapCache(PLAT_CHART_CACHE)
PLAT_SHEET_BY_ID=ManagedIDMapCache(PLAT_SHEET_CACHE)
UNDERRATED_BY_ID=ManagedIDMapCache(UR_CACHE)


_DIFFICULTY_MAPPINGS:dict[str,Difficulty]={
}
_LENGTH_MAPPINGS:dict[str,Length]={l.name.lower():l for l in Length}

def update_diff_aliases():
    _DIFFICULTY_MAPPINGS.update({k.name.lower():k for k in Difficulty})
    
    ALIASES={
        Difficulty.EASY_DEMON:["ezd","ezp"],
        Difficulty.MEDIUM_DEMON:["med","mep"],
        Difficulty.HARD_DEMON:["hdd","hdp"],
        Difficulty.INSANE_DEMON:["insd","insp"],
        Difficulty.EXTREME_DEMON:["exd","exp"],
        Difficulty.ANY_DEMON:["demon","pemon","d"],
        Difficulty.AUTO:["at"],
        Difficulty.EASY:["ez"],
        Difficulty.NORMAL:["nm"],
        Difficulty.HARD:["hd"],
        Difficulty.HARDER:["hr"],
        Difficulty.INSANE:["in"]
    }
    for diff,keys in ALIASES.items():
        for key in keys:
            _DIFFICULTY_MAPPINGS[key]=diff

class SearchTypeArg:
    search_type:LevelSearchType
    help_str:str
    def __init__(self,search_type:LevelSearchType,help_str:str) -> None:
        self.search_type=search_type
        self.help_str=help_str
        
_SEARCH_TYPES:dict[str,SearchTypeArg]={
    "search":SearchTypeArg(LevelSearchType.SEARCH,"Search (Default)"),
    "user":SearchTypeArg(LevelSearchType.FROM_USER,"User's Levels"),
    "recent":SearchTypeArg(LevelSearchType.RECENT,"Recent"),
    "downloads":SearchTypeArg(LevelSearchType.DOWNLOADS,"Most Downloaded"),
    "likes":SearchTypeArg(LevelSearchType.LIKES,"Most Liked"),
    "trending":SearchTypeArg(LevelSearchType.TRENDING,"Trending"),
    "awarded":SearchTypeArg(LevelSearchType.AWARDED,"Awarded"),
    "daily":SearchTypeArg(LevelSearchType.DAILY,"Daily Levels"),
    "weekly":SearchTypeArg(LevelSearchType.WEEKLY,"Weekly Levels"),
    "featured":SearchTypeArg(LevelSearchType.FEATURED,"Featured Levels"),
}

class BoolFlagArg:
    attr_name:str
    help_str:str
    def __init__(self,attr_name:str,help_str:str) -> None:
        self.attr_name=attr_name
        self.help_str=help_str
    def apply(self,searchArgs:LevelSearchArgs,value:bool):
        setattr(searchArgs,self.attr_name,bool(value))

_BOOL_FLAGS:dict[str,BoolFlagArg]={
    "--2-player":BoolFlagArg("twoPlayer","2-Player"),
    "--coins":BoolFlagArg("coins","Has Coins"),
    "--featured":BoolFlagArg("featured","Featured"),
    "--epic":BoolFlagArg("epic","Epic"),
    "--legendary":BoolFlagArg("legendary","Legendary"),
    "--mythic":BoolFlagArg("mythic","Mythic"),
    "--nostar":BoolFlagArg("noStar","No Star (Unrated)"),
    "--original":BoolFlagArg("original","Original")
}

update_diff_aliases()

gdsearch = on_command("gdsearch")
@gdsearch.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        searchArgs=LevelSearchArgs()
        
        parser=ArgParser("gdsearch")
        
        group_length=parser.add_mutually_exclusive_group()
        group_length.add_argument('--classic',help='Classic only',action='store_true')
        group_length.add_argument('--plat',help='Platformer only',action='store_true')
        
        group_length.add_argument('-l',help='length',type=str,default="")
        
        parser.add_argument('--song',help='Song ID (prefix _ for official songs)',type=str,default=0)
        
        parser.add_argument('-d',help='Difficulty',type=str,default="")
        parser.add_argument('-v',help='Show Other Info',action='store_true')
        parser.add_argument('--text',help='Plain Text',action='store_true')
        parser.add_argument('-i',help='Show Thumbnail',action='store_true')
        parser.add_argument('-a',help='Include Unrated',action='store_true')
        parser.add_argument('-u',help="User's Levels",action='store_true')
        
        parser.add_argument('-p',help='Page',type=int,default=0)
        
        parser.add_argument('-t', type=str, help=f"search type ({' | '.join(_SEARCH_TYPES)})", default='search')
        
        filters=parser.add_argument_group("Search Filters")
        for key,entry in _BOOL_FLAGS.items():
            filters.add_argument(key,help=entry.help_str,action='store_true')
        
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        searchArgs.setSearch(search)
        
        classic_only=bool(parsed.classic)
        plat_only=bool(parsed.plat)
        
        song_arg=str(parsed.song)
        if song_arg:
            song_id=int(song_arg.removeprefix("_"))
            searchArgs.setSong(song_id,not song_arg.startswith("_"))
        
        if parsed.u:
            search_type_str="user"
        else:
            search_type_str=str(parsed.t).lower()
            
        search_type=_SEARCH_TYPES.get(search_type_str)
            
        if not search_type:
            raise ValueError(f"未知搜索类型 {search_type_str}. 可用类型: {','.join(_SEARCH_TYPES.keys())}")
        
        searchArgs.setSearchType(search_type.search_type)
                
        for key,entry in _BOOL_FLAGS.items():
            name=key.removeprefix("-").removeprefix("-").replace("-","_")
            if getattr(parsed,name):
                entry.apply(searchArgs,True)
        
        lengths:list[Length]=[]
        
        for l in str(parsed.l).lower().split(","):
            if l in _LENGTH_MAPPINGS:
                lengths.append(_LENGTH_MAPPINGS[l])
        
        difficulty:list[Difficulty]=[]
        
        for diff in str(parsed.d).lower().split(","):
            if diff in _DIFFICULTY_MAPPINGS:
                difficulty.append(_DIFFICULTY_MAPPINGS[diff])
                if diff.endswith("p") or diff=="pemon":
                    plat_only=True
        
        logger.info(locals())
        
        include_unrated=bool(parsed.a or parsed.nostar)
        page=int(parsed.p)
        
        if classic_only:
            searchArgs.setLength([Length.TINY,Length.SHORT,Length.MEDIUM,Length.LONG,Length.XL])
        elif plat_only:
            searchArgs.setLength([Length.PLAT])
        else:
            searchArgs.setLength(lengths)
            
        searchArgs.setDifficulty(difficulty)
        searchArgs.setStar(not include_unrated)
        searchArgs.setPage(page)
        
        verbose=bool(parsed.v)
        force_text=bool(parsed.t)
        show_thumbnail=bool(parsed.i)
        
        logger.info(searchArgs.getData())
        
    except Exception as e:
        await gdsearch.finish(str(e))
        return
    
    lines=bbot_api.TextImageMessage.build(bot)
    
    if searchArgs.getSearchType()==LevelSearchType.FROM_USER:
        levels,pageinfo=getLevelsFromUser(searchArgs)
    else:
        levels,pageinfo=getLevelSearch2(searchArgs)
        
    if not include_unrated:
        lines.addLine("默认只搜索 Rated 关卡. -a 以搜索全部关卡.")
    
    if not isinstance(levels,list) or not pageinfo.success():
        lines.addLine("查找出错."+pageinfo.status.value)
        await gdsearch.finish(lines.msg)
        return
    if levels.__len__()==0:
        lines.addLine("没有查找到任何关卡.")
        await gdsearch.finish(lines.msg)
        return
    elif levels.__len__()>1:
        lines.addLine("找到多个关卡,请用id选择:")
        lines.addLine(f"第 {page}/{math.ceil(pageinfo.total/pageinfo.amount)} 页 ({pageinfo.offset}-{pageinfo.offset+pageinfo.amount}/{pageinfo.total})")
        for l in levels:
            lines.addLine(repr_level(l))
            if l.is_plat():
                lines.addText("".join([f" E{l2.enj or '-'} W{l2.weight or '-'} P{l2.pemon or '-'}" for l2 in PLAT_CHART_BY_ID.get_for_id(l.id)]))
            
        await gdsearch.finish(await bbot_api.auto_pack_message(bot,lines.msg,6))
        return
    
    level=levels[0]
    
    level2=None
    if verbose:
        level2=downloadLevel2(level.id)
        
    supports_image=(isinstance(bot,OBBot) or isinstance(bot,DCBot))
    enable_image=(not force_text) and supports_image
    
    info_image=False
    
    dc_entry=None
    dc_entries=PLAT_CHART_BY_ID.get_for_id(level.id)
    if dc_entries:
        dc_entry=dc_entries[0]
    
    nlwlike_entry=None
    nlwlike_entries=PLAT_SHEET_BY_ID.get_for_id(level.id)
    nlwlike_entries.sort(key=lambda x: 1 if x.is_legacy() else 0)
    
    if nlwlike_entries:
        nlwlike_entry=nlwlike_entries[0]
    
    underrated_entry=None
    underrated_entries=UNDERRATED_BY_ID.get_for_id(level.id)
    if underrated_entries:
        underrated_entry=underrated_entries[0]
    
    song=gd.getSong(level.songID)
    
    # Image Sections
    if enable_image:
        req_id_base=bbot_api.getid(event)
        extra_render_args:dict[str,Any]={}
        if dc_entry:
            extra_render_args.update({
                "weight":str(dc_entry.weight or '-'),
                "pemonlist":str(dc_entry.pemon or '-'),
                "diffchart_tier":dc_entry.tier or '',
                "diffchart_tags":','.join(dc_entry.tags)
            })
            
        if underrated_entry:
            extra_render_args.update({
                "underrated_tier":f"{underrated_entry.tier} ({underrated_entry.get_tier_reference()})",
                "underrated_tags": ", ".join(underrated_entry.skillsets)
            })
            
        if nlwlike_entry:
            extra_render_args.update({
                "nlw_type": nlwlike_entry.sheet,
                "nlw_tier": nlwlike_entry.section,
                "nlw_tags": ", ".join(nlwlike_entry.skillsets)
            })
            
        if nlwlike_entries:
            for l in nlwlike_entries:
                if l.checkpoints: 
                    extra_render_args["checkpoints"]=l.checkpoints.replace("∞","Infinite")
                    break
            
        if level2:
            extra_render_args.update({
                "length2":format_verify_time(level2.verification_time),
                "song_info": f"Songs: {len(level2.song_ids or '')}, SFXs: {len(level2.sfx_ids or '')}"
            })
        
        img=await render_api.render_level(req_id_base+"_base",
                        level_id=level.id,
                        level_name=level.name,
                        song_id=level.songID,
                        song_author=song.artistName if song else "Unknown",
                        song_name=song.name if song else "Unknown",
                        creator=level.creator,
                        stars=level.stars,
                        length=level.get_length().get_name(),
                        difficulty=level.get_difficulty().value,
                        feature_level=level.epic+1 if level.featured>0 else 0,
                        is_plat=level.is_plat(),
                        coins=level.coins,
                        bronze_coins=not level.verifiedCoins,
                        downloads=level.downloads,
                        likes=level.likes,
                        scene_type="level_large",
                        thumbnail=getThumbnailUrl(level.id),
                        description=level.get_description(),
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
    
    if not verbose:
        lines.addLine(f"-v 参数查询具体时长, 上传/更新日期, 及额外曲目.")
        
        
    lines.addLine(f"Version: {level.version} Game ver.: {level.game_version}")
    lines.addLine(f"2P: {level.two_player}, Objects: {level.objects}")
    
    if not info_image:
        lines.addLine(f"Length: {gd.Length(level.length).name}")
        if level2:
            lines.addText(f" ({format_verify_time(level2.verification_time)})")
            
        lines.addLine(f"Coins: {level.coins}")
        if not level.verifiedCoins:
            lines.addText(" (Bronze)")
        if song:
            lines.addLine(f"Song: {song.name} by {song.artistName} ({song.id})")
            
        if level2:
            lines.addLine(f"Songs: {len(level2.song_ids or '')}, SFXs: {len(level2.sfx_ids or '')}")
        
    if level2:
        lines.addLine(f"Upload/update: {level2.upload_date}/{level2.update_date}")
        
    if underrated_entries:
        lines.addLine("--Underrated Levels--")
        for e in underrated_entries:
            lines.addLine(formatUnderrated(e,False,True))
    
    if level.is_plat():
        
        if dc_entries:
            lines.addLine("--Difficulty Chart--")
        for e in dc_entries:
            lines.addLine(formatters.formatDiffChart(e,False,True))
        
        if nlwlike_entries:
            lines.addLine("--NLW/IDS/HDS--")
        for e in nlwlike_entries:
            lines.addLine(formatters.formatListsLevel(e,False,True))
            
            
        
    
    # if not (classic_only or plat_only or demon):
    #     lines.append("使用-c、-p、-d参数, 可显示Classic、Plat与Demon关卡的详细计数")

    if show_thumbnail and supports_image:
        thumb=getThumbnail(level.id)
        if thumb:
            lines.addImage(thumb)
            
    # Others (Text)
    if verbose:
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


def format_verify_time(frame_count: int | None, fps: int = 240) -> str:
    """将验证用时（帧）格式化为 1h 1m 1s 形式，低于 1h/1m 时隐藏对应段落。"""
    if frame_count is None:
        return ""
    total_sec = frame_count // fps
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s or not parts:
        parts.append(f"{s}s")
    return " ".join(parts)