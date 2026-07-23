from argparse import Namespace
import json
import os
import threading
import time
from typing import Any, TypeVar
from nonebot import on_command,logger,get_plugin_config
from nonebot.permission import SUPERUSER
from nonebot import get_driver,require
from nonebot.internal.matcher import Matcher

from .config import Config

from . import plat_sheets,levelid_filler

from .data_cache import BaseCache,CacheWithIDMap

require('gd_api')
from ..gd_api import gd,thumbs,gddl,aredl,pemonlist

from .underrated_data import UnderratedLevel,get_all_underrated
from .models import GDDLLevel,AREDLLevel,PemonlistLevel
from .plat_sheets import PlatChartEntry

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from apscheduler.triggers.cron import CronTrigger

plugin_config = get_plugin_config(Config)

driver=get_driver()

PLAT_CHART_CACHE = CacheWithIDMap(plat_sheets.PlatChartEntry,"platsearch_cache/plat_chart_cache.json",
    plugin_config.sheets_update_interval,name="Plat Chart cache")
PLAT_SHEET_CACHE = CacheWithIDMap(plat_sheets.TheListsEntry,"platsearch_cache/plat_sheet_cache.json",
    plugin_config.sheets_update_interval,name="Plat Sheet cache")
UNDERRATED_CACHE = CacheWithIDMap(UnderratedLevel,"platsearch_cache/underrated_cache.json",
    plugin_config.sheets_update_interval,"Underrated Cache").set_update_function(get_all_underrated)
PEMONLIST_CACHE = CacheWithIDMap(PemonlistLevel,"",3600,"Pemonlist Levels")

AREDL_CACHE = CacheWithIDMap(AREDLLevel,"",3600,"AREDL Levels")

caches:list[BaseCache]=[PLAT_CHART_CACHE,PLAT_SHEET_CACHE,UNDERRATED_CACHE,
                        PEMONLIST_CACHE,AREDL_CACHE]

@driver.on_startup
async def load():
    os.makedirs("platsearch_cache",exist_ok=True)
    levelid_filler.FILLER_MAPPING.load()
    gddl.CACHE.get()
    
    for cache in caches:
        cache.getOrUpdate()
        logger.info(cache.getLogInfo())
        
    
    trigger=CronTrigger.from_crontab('*/30 * * * *') # Update every 30 mins
    scheduler.add_job(update_caches,trigger,args=[False],id="Plat Cache Update",misfire_grace_time=1800)
    
    
async def update_caches(force_gddl:bool=False):
    os.makedirs("platsearch_cache",exist_ok=True)
    
    levelid_filler.FILLER_MAPPING.load()
    if force_gddl:
        await gddl.CACHE.updateNow()
    else:
        await gddl.CACHE.getOrUpdate()
    
    for cache in caches:
        threading.Thread(target=threaded_update_cache,args=[cache],name=cache.name).start()
        
@PLAT_CHART_CACHE.set_update_function
def get_plat_chart():
    results=plat_sheets.get_plat_chart()
    match_ids_for_levels(results,"cache/plat_chart_unmatched.json")
    return results

def fill_pemonlist_for_levels(levels:list[PlatChartEntry]):
    for l in levels:
        pemonlist_levels=PEMONLIST_CACHE.get_for_id(l.id)
        if not pemonlist_levels: continue
        p=pemonlist_levels[0]
        l.pemon=p.placement
    return

@PLAT_SHEET_CACHE.set_update_function
def get_3_lists():
    results=plat_sheets.get_3_lists()
    match_ids_for_levels(results,"cache/plat_sheet_unmatched.json")
    return results

@PEMONLIST_CACHE.set_update_function
def getPemonlistLevels():
    results=pemonlist.getPemonlistLevels()
    if not results:
        return []
    return [PemonlistLevel(l) for l in results]

@AREDL_CACHE.set_update_function
def getAREDLMerged():
    results=[]
    results.extend(aredl.getAREDLLevels(False) or [])
    results.extend(aredl.getAREDLLevels(True) or [])
    if not results:
        return []
    return [AREDLLevel(l) for l in results]

def match_ids_for_levels(entries:list[levelid_filler.ENTRY_TYPE],logfile:str=""):
    levels_not_matched=levelid_filler.fillIDsForEntries(entries)
    if levels_not_matched:
        jsondata=[]
        for l in levels_not_matched:
            jsondata.append({"level":l.to_dict(),"matches":levelid_filler.FILLER_MAPPING.getEntriesForName(l.name)})
            
        if logfile:
            with open(logfile,"w") as f:
                json.dump(jsondata,f,indent=2)

def threaded_update_cache(cache:BaseCache):
    cache.update()
    logger.info(f"Loaded {cache.entries.__len__()} entries into {cache.name}, expiring at {time.ctime(cache.expiration_time)}")
    

    
platupdate = on_command("platupdate",permission=SUPERUSER)
@platupdate.handle()
async def _():
    await platupdate.send("开始刷新platsearch缓存...\n刷新DifficultyChart...")
    PLAT_CHART_CACHE.update()
    await platupdate.send("刷新NLW/IDS/HDS...")
    PLAT_SHEET_CACHE.update()
    await platupdate.finish(f"刷新完毕. DifficultyChart:{PLAT_CHART_CACHE.entries.__len__()}, NLW/IDS/HDS:{PLAT_SHEET_CACHE.entries.__len__()})")
    return

gdupdate = on_command("gdupdate",permission=SUPERUSER)
@gdupdate.handle()
async def _():
    logger.info("Updating GD cache...")
    await gdupdate.send("开始刷新gd缓存...")
    msg=[]
    for cache in caches:
        cache.update()
        logger.info(cache.getLogInfo())
        msg.append(cache.getLogInfo())
    await gdupdate.finish(f"刷新完毕:\n"+("\n".join(msg)))
    return