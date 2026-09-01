from pathlib import Path

from ..file_based_cache import FileBasedCache
from .gddl_internal import GDDLSearchResult,getGDDLResponse,fetch_gddl_all_plat,safeFloat,safeInt
from .. import run_async
from .models import GDDLLevel,GDDLSearchLevel

from nonebot import require,get_driver

CACHE=FileBasedCache(list,fetch_gddl_all_plat,Path("cache")/"gddl_plat.json",cache_name="GDDL Platformer Cache",expiration=8640000)

# 局部测试/直接运行插件时 NoneBot 未初始化，get_driver()/require() 会抛异常。
# 此时跳过定时任务注册；正常启动时正常注册。try 块只覆盖这两个可能失败的调用。
try:
    driver=get_driver()
    require("nonebot_plugin_apscheduler")
except (ValueError, RuntimeError):
    pass
else:
    from nonebot_plugin_apscheduler import scheduler
    from apscheduler.triggers.cron import CronTrigger

    @driver.on_startup
    async def register_job():
        trigger=CronTrigger.from_crontab('0 5 * * *') # Update every day at 5:00
        scheduler.add_job(update, trigger=trigger, id="GDDL_UPDATE", misfire_grace_time=86400)

# TODO: rework to adapt new GDDL API

def parseLevelData(data:list[dict]|None):
    if not data:
        return None
    levels:dict[int,GDDLLevel]={}
    for l in data:
        level=GDDLSearchLevel.from_dict(l).to_gddl_level()
        levels[level.ID]=level
    return levels

async def getGDDLPlat_async():
    data=await CACHE.getOrUpdate()
    return parseLevelData(data)

def getGDDLPlat():
    data=CACHE.get()
    return parseLevelData(data)
    
async def update():
    await CACHE.updateNow()
    