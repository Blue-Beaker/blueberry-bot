from argparse import Namespace
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta, timezone, tzinfo
import traceback
from typing import Any, Callable, TypeVar
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

from .api.search_args import ModSearchArgs,ModStatus,Platform,Sort
from .api.api import searchModsWithArgs_async,getMod_async,getModDownloadUrl,getModVersion_async,getModVersions_async,getModIcon_async
from .api.models import Mod,Developer,Dependency

require('bbot_api')
from ..bbot_api.argparse import ArgumentError,ArgParser
from ..bbot_api import TextImageMessage,supportsImage,safeInt,safeFloat,supportsMarkdown
from .. import bbot_api
from ..bbot_api.message_compat import file
from ..bbot_api.message_compat.buttons import KBButton

geodesearch = on_command("geodesearch")
@geodesearch.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    
    if not raw_args and not event.get_message().extract_plain_text().endswith(" "):
        await geodesearch.finish('\n'.join([
            "用法: geodesearch [参数] [Mod名/ID]",
            "gdls -h 查询所有参数."]))
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
        
        parser.add_argument('--featured', action='store_true', help='Only featured mods')
        parser.add_argument('--status', type=str, help=f"Status ({' | '.join(ModStatus.__members__)})", default='')
        parser.add_argument('--sort', type=str, help=f"Sort ({' | '.join(Sort.__members__)})", default='')
        
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
        if parsed.featured:
            searchArgs.featured=True
        if parsed.status:
            status=str.upper(parsed.status)
            if status not in ModStatus.__members__:
                await geodesearch.finish(f"未知状态. 可用选项: {', '.join(ModStatus.__members__)}")
            searchArgs.status=ModStatus.__members__.get(status,None)
        if parsed.sort:
            sort=str.upper(parsed.sort)
            if sort not in Sort.__members__:
                await geodesearch.finish(f"未知排序. 可用选项: {', '.join(Sort.__members__)}")
            searchArgs.sort=Sort.__members__.get(sort,None)
        
        
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
        
    cmd=event.get_message().extract_plain_text().split()[0]
    def jump_cmd_func(modid:str):
        return cmd+" "+modid
    
    if search_result.count!=1:
        reply.addLine(f"搜索到 {search_result.count} 个结果:")
        
        for m in search_result.data:
            repr_mod(m,reply,jump_cmd_func)
        await reply.finish(geodesearch)

    m:Mod = search_result.data[0]
    # repr_mod(m,reply,jump_cmd_func)
    if bbot_api.supportsImage(bot) and m.latest_version:
        img, err = await getModIcon_async(m.id, m.latest_version.version)
        if isinstance(img,bytes):
            reply.addImage(img,m.id+".png")
    show_mod_details(m,reply)
        
    await reply.finish(geodesearch)
    
def show_mod_details(m:Mod, msg:TextImageMessage):
    msg.addLine(f"{m.name} by {','.join([u.display_name for u in m.developers])}")
    msg.addLine("")
    if m.latest_version:
        latest=m.latest_version
        msg.addLine(f"{latest.description}")
        msg.addLine("")
        msg.addLine(f"Version: {latest.version}")
        
        if latest.dependencies:
            deps:dict[str,list[Dependency]]={}
            for d in latest.dependencies:
                if d.importance not in deps:
                    deps[d.importance]=[]
                deps[d.importance].append(d)
            
            msg.addLine("")
            msg.addLine(f"Dependencies:")
            for imp,deps2 in deps.items():
                msg.addLine(f"{imp}: {','.join([d.mod_id+'='+d.version for d in deps2])}")
    
    msg.addLine("")
    msg.addLine(f"Supported versions:")
    for geode_ver,gd_ver in m.supported_versions.items():
        plats,vers=collect_gd_versions(gd_ver)
        msg.addLine(f"Geode {geode_ver}, GD {','.join(plats)}-{','.join(vers)}")
    
    if m.created_datetime:
        local_create_time=m.created_datetime.astimezone(tz=datetime.now().tzinfo)
        msg.addLine(f"Created {local_create_time}")
    if m.updated_datetime:
        local_update_time=m.updated_datetime.astimezone(tz=datetime.now().tzinfo)
        msg.addLine(f"Updated {local_update_time}")
        
def collect_gd_versions(gd_versions:dict[str,str]):
    platforms:set[str]=set()
    versions:set[str]=set()
    for k,v in gd_versions.items():
        if isinstance(v,str):
            platforms.add(str(k))
            versions.add(v)
            
    if 'mac-arm' in platforms and 'mac-intel' in platforms:
        platforms.remove('mac-arm')
        platforms.remove('mac-intel')
        platforms.add('mac')    
    if 'android64' in platforms and 'android32' in platforms:
        platforms.remove('android64')
        platforms.remove('android32')
        platforms.add('android')    
    
    return platforms,versions
    
def repr_mod(m:Mod, msg:TextImageMessage, jump_cmd_func:Callable[[str],str]|None=None):
    mod_line1=f"{m.name} by {m.owner.display_name if m.owner else ''}"
    if m.developers.__len__()>1:
        mod_line1+=f"..."
            
    msg.addLine(mod_line1)
    msg.addLine("")
    
    if not msg.supportsButton() or not jump_cmd_func:
        mod_line2=f"{m.id}\t"
    else:
        mod_line2=f"\t"
        msg.addButton(KBButton(text=m.id,command=jump_cmd_func(m.id)))
    
    if m.latest_version:
        plats,vers=collect_gd_versions(m.latest_version.gd)
        if vers:
            mod_line2 += f" GD: {','.join(vers)}"
            
    if m.created_datetime and m.updated_datetime:
        now=datetime.now(timezone.utc)
        
        mod_line2+=f" ({humanize(get_time_delta(now,m.created_datetime),short=True,precision=1)},{humanize(get_time_delta(now,m.updated_datetime),short=True,precision=1)})"
        
    msg.addText(mod_line2)
    
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

try:
    require("bbot_help")
    from ..bbot_help import addHelpFunc,getExtraRegistry
    GD_HELP=getExtraRegistry("gd")
    
    @GD_HELP.addHelpFunc
    def get_help(bot:Bot,event:Event):
        return ["geodesearch [参数] [Mod名/ID] 查询 Geode Index 上的 Mod"]
except:
    logger.error(traceback.format_exc())