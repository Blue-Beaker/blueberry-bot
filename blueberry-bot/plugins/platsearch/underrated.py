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

UNDERRATED_ID="1-Abvx7zXRAqpGFVbdTXpn6g1TRYp9WuZqW2pHWE7Dr4"
UR_AUTO = Sheet(UNDERRATED_ID,"Auto 1*!A2:G")
UR_EASY = Sheet(UNDERRATED_ID,"Easy 2*!A2:G")
UR_NORMAL = Sheet(UNDERRATED_ID,"Normal 3*!A2:G")
UR_HARD = Sheet(UNDERRATED_ID,"Hard 4-5*!A2:G")
UR_HARDER = Sheet(UNDERRATED_ID,"Harder 6-7*!A2:G")
UR_INSANE = Sheet(UNDERRATED_ID,"Insane 8-9*!A2:G")

# logger.info(UR_AUTO.get())
# logger.info(UR_EASY.get())
# logger.info(UR_NORMAL.get())
# logger.info(UR_HARD.get())
# logger.info(UR_HARDER.get())
# logger.info(UR_INSANE.get())

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
    mappings={"Auto":UR_AUTO,
                "Easy":UR_EASY,
                "Normal":UR_NORMAL,
                "Hard":UR_HARD,
                "Harder":UR_HARDER,
                "Insane":UR_INSANE}
    for name,sheet in mappings.items():
        table=sheet.get()
        if table:
            entries.extend(parse_underrated_sheet(table,name))
    return entries
        
UR_CACHE = BaseCache(UnderratedLevel,"platsearch_cache/underrated_cache.json",
                           plugin_config.sheets_update_interval).set_update_function(get_all_underrated)

driver = get_driver()
@driver.on_startup
async def load_cache():
    os.makedirs("platsearch_cache",exist_ok=True)
    threading.Thread(target=threaded_update_cache,args=[UR_CACHE,"Underrated Levels cache"]).start()
    
def threaded_update_cache(cache:BaseCache,name:str):
    cache.get()
    logger.info(f"Loaded {cache.entries.__len__()} entries into {name}, expiring at {time.ctime(cache.expiration_time)}")
    
gdur = on_command("gdur")
@gdur.handle()
async def _(args: Message = CommandArg()):
    
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
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
            if count<=3:
                reply.append(f"{l.section}-{l.tier} {l.name} by {l.creator} ({l.id})\n{",".join(l.skillsets)}\n{l.desc}")
            else:
                reply.append(f"{l.section}-{l.tier} {l.name} by {l.creator} ({l.id}) {'🌙' if 'Platformer' in l.skillsets else ''}")
    
    await gdur.finish("\n".join(reply))