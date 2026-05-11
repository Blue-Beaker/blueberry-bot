import os
import random
import re
import threading
import time
import traceback
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
import nonebot.config
from nonebot import get_driver

from .config import Config

from . import plat_sheets
from .data_cache import BaseCache

plugin_config = get_plugin_config(Config)

driver=get_driver()

PLAT_CHART_CACHE=BaseCache(plat_sheets.PlatChartEntry,"platsearch_cache/plat_chart_cache.json",
                           plugin_config.sheets_update_interval).set_update_function(plat_sheets.get_plat_chart)
PLAT_SHEET_CACHE=BaseCache(plat_sheets.TheListsEntry,"platsearch_cache/plat_sheet_cache.json",
                           plugin_config.sheets_update_interval).set_update_function(plat_sheets.get_3_lists)

@driver.on_startup
async def load_cache():
    os.makedirs("platsearch_cache",exist_ok=True)
    threading.Thread(target=threaded_update_cache,args=[PLAT_CHART_CACHE,"Plat Chart cache"]).start()
    threading.Thread(target=threaded_update_cache,args=[PLAT_SHEET_CACHE,"Plat Sheet cache"]).start()

def threaded_update_cache(cache:BaseCache,name:str):
    cache.get()
    logger.info(f"Loaded {cache.entries.__len__()} entries into {name}, expiring at {time.ctime(cache.expiration_time)}")

class SearchArgs:
    def __init__(self,text:str) -> None:
        self.page=0
        self.fuzzy=False
        
        args=text.split(" ")
        
        while args and args[0].startswith("-"):
            arg=args[0].removeprefix("-")
            args.pop(0)
            self.applyArg(arg)
            
        self.text=" ".join(args)
        # logger.info(f"Search: Page={self.page}, Fuzzy={self.fuzzy}, Text={self.text}")
        
    def applyArg(self,arg:str):
        if arg=="f":
            self.fuzzy=True
        elif re.match(r"[0-9]+",arg):
            self.page=int(arg)

platweight = on_command("platweight")
@platweight.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    text=sa.text
    page=sa.page
    
    search = text.strip().lower()
    msg=[]
    
    if not sa.fuzzy:
        msg.append(f"Exact match, use -f [levelname] for fuzzy search")
    # results:list[plat_sheets.PlatRankEntry]=[]
    # for level in plat_sheets.plat_rank_weights():
    #     if search in level.name.lower():
    #         results.append(level)
    
    results=search_in_levels(PLAT_CHART_CACHE.get(),search,sa.fuzzy)
    
    count=results.__len__()
    entries_per_page = 5
    
    results,maxpages,page=select_page(results,count,entries_per_page,page)
    
    if count==0:
        msg.append("Not found on Plat Rank")
    else:
        msg.append(f"{count} on Plat Rank (Page {page}/{maxpages}):")
        for l in results:
            msg.append(f"{l.name} ({l.weight_type}) Weight:{l.weight}")
    await platweight.send("\n".join(msg))
    
platsheet = on_command("platsheet")
@platsheet.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    text=sa.text
    page=sa.page
    
    search = text.strip().lower()
    msg=[]
    
    if not sa.fuzzy:
        msg.append(f"Exact match, use -f [levelname] for fuzzy search")
    # results=level_in_three_sheets(search)
    
    results=search_in_levels(PLAT_SHEET_CACHE.get(),search,sa.fuzzy)
    
    
    count=results.__len__()
    
    entries_per_page = 3
    
    results:list[plat_sheets.TheListsEntry]
    results,maxpages,page=select_page(results,count,entries_per_page,page)
        
    if count==0:
        msg.append("Not found on the sheets")
    else:
        msg.append(f"{count} on sheets (Page {page}/{maxpages}):")
        
        for level in results:
            msg.append(f"{level.name} by {level.creator} ({level.sheet} {level.section}):")
            msg.append(f"Checkpoints: {level.checkpoints}, Skillsets: {",".join(level.skillsets)}")
            msg.append(f"Description: {level.description}")
        
    await platsheet.send("\n".join(msg))


platsearch = on_command("platsearch")
@platsearch.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    text=sa.text
    page=sa.page
    
    search = text.strip().lower()
    
    msg:list[str]=[]
    
    if not sa.fuzzy:
        msg.append(f"Exact match, use -f [levelname] for fuzzy search")
    # results:list[plat_sheets.PlatChartEntry]=[]
    # levels=plat_sheets.get_plat_chart()
    
    # for l in levels:
    #     if search in l.name.lower():
    #         results.append(l)
    results=search_in_levels(PLAT_CHART_CACHE.get(),search,sa.fuzzy)
    
    count=results.__len__()
    entries_per_page = 5
    
    results,maxpages,page=select_page(results,count,entries_per_page,page)
    
    if not count:
        msg.append(f"Not found")
    else:
        msg.append(f"{count} found (Page {page}/{maxpages}):")
        for l in results:
            line:list[str]=[l.name]
            if l.id>=0:
                line.append(f" ({l.id})")
            if l.tier:
                line.append(f"(T{l.tier})")
            if l.tags:
                line.append(f"\nTags: {','.join(l.tags)}")
            rankline=[]
            if l.enj and l.enj!="/":
                rankline.append(f"Enj: {l.enj}")
            if l.tpl and l.weight and l.tpl==l.weight:
                rankline.append(f"TPL/Weight: {l.tpl}")
            else:
                if l.tpl:
                    rankline.append(f"TPL: {l.tpl}")
                if l.weight:
                    rankline.append(f"Weight: {l.weight}")
            if l.pemon:
                rankline.append(f"Pemonlist: {l.pemon}")
                
            if rankline:
                line.append("\n"+",".join(rankline))
            
            msg.append("".join(line))
        
    await platsearch.send("\n".join(msg))
    
    
platskill = on_command("platskill")
@platskill.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    search=sa.text
    page=sa.page
    
    msg=[]
    # If no args present, list all skillsets
    if not sa.text:
        the_lists=PLAT_SHEET_CACHE.get()
        skills=[]
        for l in the_lists:
            for s in l.skillsets:
                if s not in skills:
                    skills.append(s)
        msg.append(f"There are {skills.__len__()} skills.")
        msg.append(f"Use '-platskill skill1,skill2...' to filter levels by skillsets.")
        msg.append(f"Example: -platskill {random.choice(skills)}")
        await platskill.send("\n".join(msg))
        return
        
    
    results:list[plat_sheets.TheListsEntry]=skill_in_three_sheets(search)
    
    count=results.__len__()
    entries_per_page = 5
    
    results,maxpages,page=select_page(results,count,entries_per_page,page)
        
    if not count:
        msg.append(f"No levels found with skill {search}")
    else:
        msg.append(f"{count} levels found with skills (Page {page}/{maxpages}):")
        msg.extend([f"{l.name} by {l.creator}" for l in results])
    
    await platskill.send("\n".join(msg))

def level_in_three_sheets(search:str):
    result:list[plat_sheets.TheListsEntry]=[]
    the_lists=plat_sheets.get_3_lists()
    for level in the_lists:
        if(search in level.name.lower()):
            result.append(level)
    return result

skill_groups=[["dash orbs","wavedash"]]

def skill_in_three_sheets(search:str):
    result:list[plat_sheets.TheListsEntry]=[]
    the_lists=PLAT_SHEET_CACHE.get()
    split:list[str]=[t.strip().lower() for t in search.split(",")]
    
    for level in the_lists:
        lskills=[s.lower() for s in level.skillsets]
        for group in skill_groups:
            intersect=list(set(group) & set(lskills))
            if intersect:
                lskills=list(set(group) | set(lskills))
        matched=True
        for s in split:
            if s not in lskills:
                matched=False
                break
        if matched:
            result.append(level)
    return result

T = TypeVar("T", bound=Any)
def select_page(results:list[T],count:int,entries_per_page:int,page:int):
    maxpages=1+((count-1)//entries_per_page)
    page=max(1,min(page,maxpages))
    if count>entries_per_page:
        results=results[(page-1)*entries_per_page:min(page*entries_per_page,count)]
    return results,maxpages,page


L = TypeVar("L", bound=plat_sheets.LevelEntry)
def search_in_levels(levels:list[L],search:str,fuzzy:bool=False):
    result:list[L]=[]
    for level in levels:
        if level.matchesName(search,fuzzy):
            result.append(level)
    return result