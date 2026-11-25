from argparse import Namespace
import json
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
            reply.addLine(f"{m.id} {m.name} by {m.owner.display_name if m.owner else ''} ({m.created_datetime},{m.updated_datetime})")
        await reply.finish(geodesearch)

    m:Mod = search_result.data[0]
    reply.addLine(f"{m.id} {m.name} by {m.owner.display_name if m.owner else ''} ({m.created_datetime},{m.updated_datetime})")
        
    await reply.finish(geodesearch)