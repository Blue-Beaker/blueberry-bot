from pathlib import Path
import sys
from typing import Any
import httpx
from .. import run_async

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.file_based_cache import FileBasedCache
    from plugins.gd_api import run_async
else:
    from ..file_based_cache import FileBasedCache
    from .. import run_async

class Level:
    level_id:int
    name:str
    publisher_id:str
    position:int
    points:int
    tags:list[str]
    legacy:bool
    
    def to_dict(self) -> dict:
        return self.__dict__
    def load_dict(self,data:dict):
        for level_key in ["level_id","name","position","publisher_id","points","tags","legacy"]:
            self.__dict__[level_key]=data.get(level_key)
        return self
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.load_dict(data)
        return inst
    
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} by {self.publisher_id} {self.level_id}"

async def getResp(url:str):
    headers = {
        "User-Agent": "",
        'accept': 'application/json' 
    }
    async with httpx.AsyncClient(timeout=30) as client:
        req = await client.get(url, headers=headers)
    if req.status_code!=200:
        return None
    else:
        return req.json()
async def aredlResp():
    return await getResp("https://api.aredl.net/v2/api/aredl/levels")
async def areplResp():
    return await getResp("https://api.aredl.net/v2/api/arepl/levels")

CACHE_CLASSIC=FileBasedCache(dict,aredlResp,Path("cache")/"aredl_classic.json",cache_name="AREDL_Classic Cache")
CACHE_PLAT=FileBasedCache(dict,areplResp,Path("cache")/"aredl_plat.json",cache_name="AREDL_Plat Cache")

async def getAREDLLevels_async(plat:bool=False):
    if plat:
        data=await CACHE_PLAT.getOrUpdate()
    else:
        data=await CACHE_CLASSIC.getOrUpdate()
    if not data:
        return None
    
    levels:list[Level]=[]
    for l in data:
        try:
            levels.append(Level().load_dict(l))
        except:
            pass
    if not levels:
        return None
    return levels

def getAREDLLevels(plat:bool=False):
    return run_async(getAREDLLevels_async(plat))

if __name__ == "__main__":
    import asyncio
    async def _test():
        print(await getAREDLLevels_async())
        print(await getAREDLLevels_async(True))
    asyncio.run(_test())