from argparse import Namespace
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.exception import MatcherException
import nonebot.config
from nonebot import get_driver,require
from nonebot.internal.matcher import Matcher

from .config import Config

from .api.search_args import ModSearchArgs,Platform
from .api.api import searchModsWithArgs_async,getMod_async,getModDownloadUrl,getModVersion_async,getModVersions_async
from .api.models import Mod,Developer,Dependency

require('bbot_api')
from ..bbot_api.argparse import ArgumentError,ArgParser
from ..bbot_api import TextImageMessage,supportsImage,safeInt,safeFloat,supportsMarkdown
from .. import bbot_api
from ..bbot_api.message_compat import file

geodesearch = on_command("geodesearch")
@geodesearch.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        searchArgs=ModSearchArgs()
        parser=ArgParser("geodesearch")
        parser.add_argument('search', nargs='*', type=str, help='search string')
        
        parser.add_argument('-p',help='Page',type=int,default=1)
        parser.add_argument('--pagesize',help='Page size',type=int,default=10)
        
        parser.add_argument('--dev',help='Developer',type=str,default='')
        parser.add_argument('--tags',help='Tags',type=str,default='')
        
        parser.add_argument('--gd',help='GD version',type=str,default='')
        parser.add_argument('--geode',help='Geode version',type=str,default='')
        
        parser.add_argument('--platform', type=str, help=f"Platform ({' | '.join(Platform.__members__)})", default='')
        
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        searchArgs.query=search
        searchArgs.page=int(parsed.p)
        searchArgs.per_page=int(parsed.pagesize)
        if parsed.dev:
            searchArgs.developer=str(parsed.dev)
        if parsed.tags:
            searchArgs.tags=[s.strip() for s in str(parsed.tags).split(",")]
        if parsed.gd:
            searchArgs.gd=parsed.gd
        if parsed.geode:
            searchArgs.geode=parsed.geode
        if parsed.platform:
            platform=str.upper(parsed.platform)
            if platform not in Platform.__members__:
                await geodesearch.finish(f"未知平台. 可用选项: {', '.join(Platform.__members__)}")
            searchArgs.platform=Platform.__members__.get(platform,None)
        
        
        logger.info(f"Geode search: {searchArgs.__dict__}")
        
    except Exception as e:
        if isinstance(e,MatcherException):
            raise e
        await geodesearch.finish(str(e))
        
    reply=TextImageMessage.build(bot)
    
    search_result, err = await searchModsWithArgs_async(args=searchArgs)
    if err:
        reply.addLine(f"错误: {err}")
        await reply.finish(geodesearch)
    elif not search_result:
        reply.addLine(f"错误: 没有返回结果")
        await reply.finish(geodesearch)
    
    if search_result.count!=1:
        reply.addLine(f"搜索到 {search_result.count} 个结果:")
        
        for m in search_result.data:
            reply.addLine(repr_mod_line(m))
        await reply.finish(geodesearch)

    m:Mod = search_result.data[0]
    reply.addLine(repr_mod_line(m))
        
    await reply.finish(geodesearch)
    
def repr_mod_line(m:Mod):
    mod_line=f"{m.name} by {m.owner.display_name if m.owner else ''}"
    if m.developers.__len__()>1:
        mod_line+=f"..."
            
    mod_line+=f"\n{m.id}\t"
    
    if m.latest_version:
        latest_gd_vers:set[str] = set()
        for k,v in m.latest_version.gd.items():
            if isinstance(v,str):
                latest_gd_vers.add(v)
        if latest_gd_vers:
            mod_line += f" GD: {','.join(latest_gd_vers)}"
            
    if m.created_datetime and m.updated_datetime:
        now=datetime.now(timezone.utc)
        
        mod_line+=f" ({humanize(get_time_delta(now,m.created_datetime),short=True,precision=1)},{humanize(get_time_delta(now,m.updated_datetime),short=True,precision=1)})"
        
    return mod_line
    
def get_time_delta(base:datetime, cmp:datetime):
    delta=base-cmp
    return delta

# (秒数, 长格式单数, 长格式复数, 短格式)
_TIME_UNITS:list[tuple[int,str,str,str]]=[
    (86400*365,"year","years","y"),
    (86400*30,"month","months","mo"),
    (86400,"day","days","d"),
    (3600,"hour","hours","h"),
    (60,"minute","minutes","m"),
    (1,"second","seconds","s"),
]

def humanize(delta:timedelta, short:bool=False, precision:int=1, ago:bool=True) -> str:
    """把 timedelta 转成可读字符串。

    :param short: True 用短格式（2d 5h），False 用长格式（2 days 5 hours）
    :param precision: 最多显示几级单位，1 表示只显示最大单位
    :param ago: 长格式下是否追加 " ago"（短格式忽略）

    示例:
        humanize(timedelta(days=2))                    -> "2 days ago"
        humanize(timedelta(days=2), short=True)        -> "2d"
        humanize(timedelta(days=2, hours=5), precision=2) -> "2 days 5 hours ago"
        humanize(timedelta(days=2, hours=5), short=True, precision=2) -> "2d 5h"
    """
    s=int(delta.total_seconds())
    if s<0:
        s=-s

    parts:list[str]=[]
    for unit_s,long_single,long_plural,short_s in _TIME_UNITS:
        if len(parts)>=precision:
            break
        if s<unit_s:
            continue
        n=s//unit_s
        s-=n*unit_s
        if short:
            parts.append(f"{n}{short_s}")
        else:
            parts.append(f"{n} {long_single if n==1 else long_plural}")

    if not parts:
        parts.append("0s" if short else "0 seconds")

    result=" ".join(parts)
    if not short and ago:
        result+=" ago"
    return result