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
import nonebot.config
from nonebot import get_driver,require
from nonebot.internal.matcher import Matcher

from .config import Config

from .api.search_args import ModSearchArgs,Platform
from .api.api import searchModsWithArgs_async,getMod_async,getModDownloadUrl,getModVersion_async,getModVersions_async

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
        
        parser.add_argument('--platform', type=str, help=f"Platform ({' | '.join(Platform.__members__)})", default='search')
        
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        searchArgs.query=search
        searchArgs.page=int(parsed.p)
        searchArgs.per_page=int(parsed.pagesize)
        searchArgs.developer=str(parsed.dev) or None
        searchArgs.tags=[s.strip() for s in str(parsed.tags).split(",")] if parsed.tags else None
        searchArgs.gd=parsed.gd or None
        searchArgs.geode=parsed.geode or None
        searchArgs.platform=Platform.__members__.get(parsed.platform,None)
        
        print(searchArgs.__dict__)
        
    except Exception as e:
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
            reply.addLine(f"{m.id} {m.name} by {m.owner.display_name if m.owner else ''} ({m.created_at},{m.updated_at})")
        
    await reply.finish(geodesearch)