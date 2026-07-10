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

from .utils import select_page

plugin_config = get_plugin_config(Config)

class UnderratedLevel(LevelEntry):
    section:str
    tier:int
    id:int
    creator:str
    skillsets:list[str]
    desc:str
    def __init__(self) -> None:
        super().__init__()
        self.section=""
        self.tier=-1
        self.id=-1
        self.creator=""
        self.skillsets=[]
        self.desc=""
    def update(self,line:list[str]):
        self.tier=safeInt(line[0])
        self.name=line[1]
        self.creator=line[2]
        self.id=safeInt(line[3])
        self.skillsets=[s.strip() for s in line[4].split(",")]
        self.desc=line[5]
        return self
    def get_tier_reference(self):
        return get_tier_reference(self.section,self.tier)

UNDERRATED_ID="1-Abvx7zXRAqpGFVbdTXpn6g1TRYp9WuZqW2pHWE7Dr4"
UR_AUTO = Sheet(UNDERRATED_ID,"Auto 1*!A2:G")
UR_EASY = Sheet(UNDERRATED_ID,"Easy 2*!A2:G")
UR_NORMAL = Sheet(UNDERRATED_ID,"Normal 3*!A2:G")
UR_HARD = Sheet(UNDERRATED_ID,"Hard 4-5*!A2:G")
UR_HARDER = Sheet(UNDERRATED_ID,"Harder 6-7*!A2:G")
UR_INSANE = Sheet(UNDERRATED_ID,"Insane 8-9*!A2:G")

class Sections(Enum):
    AUTO="Auto"
    EASY="Easy"
    NORMAL="Normal"
    HARD="Hard"
    HARDER="Harder"
    INSANE="Insane"
    
TIERS_MAPPING={
    Sections.EASY:("Easy+","Normal","Normal+","Hard",">Hard"),
    Sections.NORMAL:("Normal+","Hard","Hard+","Harder",">Harder"),
    Sections.HARD:("Harder","Harder-Insane","Insane","Insane-EZD",">EZD"),
    Sections.HARDER:("Insane","EZD","EZD-MED","MED",">MED"),
    Sections.INSANE:("EZD","EZD-MED","MED","MED-HDD",">HDD")
}

def get_tier_reference(section:str,tier:int):
    tier=max(min(tier,5),1)
    if section not in Sections:
        return ""
    mapping=TIERS_MAPPING.get(Sections(section))
    if not mapping:
        return ""
    return mapping[tier-1]

def parse_underrated_sheet(table:list[list[str]],section:str|None=None):
    entries:list[UnderratedLevel]=[]
    for line in table:
        while(line.__len__()<6):
            line.append("")
        if not line[0]:
            break
        entry=UnderratedLevel().update(line)
        if section:
            entry.section=section
        entries.append(entry)
    return entries

def get_all_underrated():
    entries:list[UnderratedLevel]=[]
    mappings={Sections.AUTO:UR_AUTO,
                Sections.EASY:UR_EASY,
                Sections.NORMAL:UR_NORMAL,
                Sections.HARD:UR_HARD,
                Sections.HARDER:UR_HARDER,
                Sections.INSANE:UR_INSANE}
    for section,sheet in mappings.items():
        table=sheet.get()
        if table:
            entries.extend(parse_underrated_sheet(table,section.value))
    return entries
        
UR_CACHE = BaseCache(UnderratedLevel,"platsearch_cache/underrated_cache.json",
                           plugin_config.sheets_update_interval).set_update_function(get_all_underrated)

driver = get_driver()
@driver.on_startup
async def load_cache():
    os.makedirs("platsearch_cache",exist_ok=True)
    threading.Thread(target=threaded_update_cache,args=[UR_CACHE,"Underrated Levels cache"]).start()
    
    trigger=CronTrigger.from_crontab('*/30 * * * *') # Update every 30 mins
    scheduler.add_job(threaded_update_cache,trigger,args=[UR_CACHE,"Underrated Levels cache",True],id="Underrated Levels cache",misfire_grace_time=1800)
    
def threaded_update_cache(cache:BaseCache,name:str,force:bool=False):
    if not force:
        cache.get()
    else:
        cache.update()
    logger.info(f"Loaded {cache.entries.__len__()} entries into {name}, expiring at {time.ctime(cache.expiration_time)}")
    
gdur = on_command("gdur")
@gdur.handle()
async def _(args: Message = CommandArg()):
    
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser("gdur")
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('-s',help='Section',type=str,choices=["","auto","easy","normal","hard","harder","insane"],default="")
        parser.add_argument('-t',help='Tier',type=int)
        parser.add_argument('-f',help="Fuzzy",action='store_true')
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 1
        tier=parsed.t or -1
        section=parsed.s or ""
        fuzzy=parsed.f or False
        
        if section or tier:
            fuzzy=True
        
    except Exception as e:
        await gdur.finish(str(e))
        return
    reply = []
    
    levels=UR_CACHE.get()
    levels = [l for l in levels if (l.matchesName(search,fuzzy))]
    if tier>0:
        levels=[l for l in levels if l.tier==tier]
        
    if section:
        levels=[l for l in levels if l.section.lower()==section]
        
    count=levels.__len__()
    entries_per_page=5
    results,maxpages,page=select_page(levels,count,entries_per_page,page)
    
    if count==0:
        reply.append("Not found")
    else:
        reply.append(f"{count} found (Page {page}/{maxpages}):")
    
        for l in results:
            reply.append(formatUnderrated(l,count>3))
    
    await gdur.finish("\n".join(reply))
    
def formatUnderrated(l:UnderratedLevel,compact:bool=False,exclude_base_info:bool=False):
    line=f"{l.section}-{l.tier}"
    tier_ref=l.get_tier_reference()
    if tier_ref:
        line+=f" ({tier_ref})"
    if not exclude_base_info:
        line+=f"{l.name} by {l.creator} ({l.id})"
    if not compact:
        line+=f"\n{",".join(l.skillsets)}\n{l.desc}"
    if not exclude_base_info and 'Platformer' in l.skillsets:
        line+='🌙'
    return line