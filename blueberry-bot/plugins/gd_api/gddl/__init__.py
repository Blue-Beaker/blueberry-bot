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
else:
    from ..file_based_cache import FileBasedCache
    from .gddl_internal import GDDLSearchResult,getGDDLResponse,fetch_gddl_all_plat,safeFloat,safeInt
    from .. import run_async
    
    from nonebot import require
    require("nonebot_plugin_apscheduler")
    from nonebot_plugin_apscheduler import scheduler
    from apscheduler.triggers.cron import CronTrigger

class GDDLLevel:
    ID:int=0
    Rating:float|None=None
    Enjoyment:float|None=None
    EnjoymentCount:int=0
    Popularity:float=0
    Length:int=0
    # Meta
    Name:str=""
    Description:str=""
    # Meta/Publisher/name
    Publisher:str=""
    def load(self,data:dict):
        self.ID=safeInt(data.get("ID"),self.ID)
        self.Rating=safeFloat(data.get("Rating"),self.Rating)
        self.Enjoyment=safeFloat(data.get("Enjoyment"),self.Enjoyment)
        self.EnjoymentCount=safeInt(data.get("EnjoymentCount"),self.EnjoymentCount)
        self.Popularity=safeFloat(data.get("Popularity"),self.Popularity)
        self.Length=safeInt(data.get("Length"),self.Length)
        
        meta=data.get("Meta")
        if isinstance(meta,dict):
            self.Name=meta.get("Name","")
            self.Description=meta.get("Description","")
            
            publ=meta.get("Publisher")
            if isinstance(publ,dict):
                self.Publisher=publ.get("name","")
            
        return self
    def __repr__(self) -> str:
        return f"GDDLLevel[{self.Name} by {self.Publisher} {self.ID}]"

CACHE=FileBasedCache(list,fetch_gddl_all_plat,Path("cache")/"gddl_plat.json",cache_name="GDDL Platformer Cache",expiration=8640000)

async def getGDDLPlat_async():
    data=await CACHE.getOrUpdate()
    if not data:
        return None
    levels:dict[int,GDDLLevel]={}
    for l in data:
        level=GDDLLevel().load(l)
        levels[level.ID]=level
    return levels

def getGDDLPlat():
    data=CACHE.get()
    if not data:
        return None
    levels:dict[int,GDDLLevel]={}
    for l in data:
        level=GDDLLevel().load(l)
        levels[level.ID]=level
    return levels
    
if __name__ == "__main__":
    import asyncio
    async def _test():
        levels=await getGDDLPlat_async()
        if levels:
            print(levels)
    asyncio.run(_test())
else:
    async def update():
        await CACHE.updateNow()
    trigger=CronTrigger.from_crontab('0 5 * * *') # Update every day at 5:00
    scheduler.add_job(update, trigger=trigger, id="GDDL_UPDATE", misfire_grace_time=86400)