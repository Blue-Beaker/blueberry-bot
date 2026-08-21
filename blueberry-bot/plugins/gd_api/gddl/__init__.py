from pathlib import Path
import sys

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.file_based_cache import FileBasedCache
    from gddl_internal import GDDLSearchResult,getGDDLResponse,fetch_gddl_all_plat,safeFloat,safeInt
    from plugins.gd_api import run_async
    from models import GDDLLevel,GDDLSearchLevel
else:
    from ..file_based_cache import FileBasedCache
    from .gddl_internal import GDDLSearchResult,getGDDLResponse,fetch_gddl_all_plat,safeFloat,safeInt
    from .. import run_async
    from .models import GDDLLevel,GDDLSearchLevel
    
    from nonebot import require
    require("nonebot_plugin_apscheduler")
    from nonebot_plugin_apscheduler import scheduler
    from apscheduler.triggers.cron import CronTrigger


CACHE=FileBasedCache(list,fetch_gddl_all_plat,Path("cache")/"gddl_plat.json",cache_name="GDDL Platformer Cache",expiration=8640000)

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
    
if __name__ == "__main__":
    import asyncio
    async def _test_raw():
        resp=await getGDDLResponse()
        if resp:
            levels=parseLevelData(resp.levels)
            print(levels)
            return levels
    async def _test():
        levels=await getGDDLPlat_async()
        if levels:
            print(levels)
    # asyncio.run(_test())
    asyncio.run(_test_raw())
else:
    async def update():
        await CACHE.updateNow()
    trigger=CronTrigger.from_crontab('0 5 * * *') # Update every day at 5:00
    scheduler.add_job(update, trigger=trigger, id="GDDL_UPDATE", misfire_grace_time=86400)