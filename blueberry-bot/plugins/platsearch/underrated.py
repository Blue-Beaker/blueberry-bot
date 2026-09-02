from enum import Enum
import os
import threading
import time
from typing import Any, TypeVar
from nonebot import get_driver, require,logger,on_command,get_plugin_config
from nonebot.adapters import Bot,Message,Event
from nonebot.params import CommandArg

from .plat_sheets import LevelEntry
from .data_cache import BaseCache
from .config import Config

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from apscheduler.triggers.cron import CronTrigger
require('bbot_api')
from ..bbot_api.sheets_api import Sheet
from ..bbot_api import safeInt
from ..bbot_api.argparse import ArgumentError,ArgParser

from .utils import select_page,has_skills
from .underrated_data import formatUnderrated,UnderratedLevel

plugin_config = get_plugin_config(Config)
    
from .gd_data import UNDERRATED_CACHE
gdur = on_command("gdur")
@gdur.handle()
async def _(args: Message = CommandArg()):
    
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser("gdur")
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('-s',help='Section',type=str,choices=["","auto","easy","normal","hard","harder","insane"],default="")
        parser.add_argument('-t',help='Tier',type=int)
        parser.add_argument('--skills',help="Skills",type=str,default=None)
        parser.add_argument('-f',help="Fuzzy",action='store_true')
        parser.add_argument('--pagesize',help="Page Size",type=int,default=10)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 1
        tier=parsed.t or -1
        section=parsed.s or ""
        fuzzy=parsed.f or False
        pagesize = int(parsed.pagesize)
        
        skills:list[str]=[t.strip().lower() for t in parsed.skills.split(",")] if parsed.skills else []
        
        if section or tier:
            fuzzy=True
        
    except Exception as e:
        await gdur.finish(str(e))
        return
    reply = []
    
    levels=UNDERRATED_CACHE.getOrUpdate()
    def levelMatchesFilter(l:UnderratedLevel):
        if str(l.getID())==search:
            return True
        if not l.matchesName(search,fuzzy):
            return False
        if skills and not has_skills(skills,l.skillsets):
            return False
        return True
        
    levels = [l for l in levels if levelMatchesFilter(l)]
    if tier>0:
        levels=[l for l in levels if l.tier==tier]
        
    if section:
        levels=[l for l in levels if l.section.lower()==section]
        
    count=levels.__len__()
    entries_per_page=pagesize
    results,maxpages,page=select_page(levels,count,entries_per_page,page)
    
    if count==0:
        reply.append("Not found")
    else:
        reply.append(f"{count} found (Page {page}/{maxpages}):")
    
        for l in results:
            reply.append(formatUnderrated(l,count>3))
    
    await gdur.finish("\n".join(reply))
    
from .gdhelp import GD_HELP
@GD_HELP.addHelpFunc
def getHelp():
    return ["gdur 查询Underrated Levels"]