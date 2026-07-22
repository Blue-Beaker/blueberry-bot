from pathlib import Path
import sys
from typing import Any
import httpx

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
    name:str
    level_id:int
    creator:str
    placement:int
    def to_dict(self) -> dict:
        return self.__dict__
    def load_dict(self,data:dict):
        for level_key in ["name","level_id","creator","placement"]:
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
        return f"{self.name} by {self.creator} {self.level_id}"

async def getPemonlistResponse():
    url="https://pemonlist.com/api/list?version=3&page=1&limit=5000"
    headers = {
        "User-Agent": ""
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        req = await client.get(url, headers=headers)
    if req.status_code!=200:
        return None
    else:
        return req.json()

CACHE=FileBasedCache(dict,getPemonlistResponse,Path("cache")/"pemonlist.json",cache_name="Pemonlist Cache")

async def getPemonlistLevels_async():
    data=await CACHE.getOrUpdate()
    if not data:
        return None
    
    levels_raw=data.get("data",[])
    levels:list[Level]=[]
    for l in levels_raw:
        try:
            levels.append(Level().load_dict(l))
        except:
            pass
    if not levels:
        return None
    return levels

def getPemonlistLevels():
    return run_async(getPemonlistLevels_async())

if __name__ == "__main__":
    import asyncio
    async def _test():
        print(await getPemonlistLevels_async())
    asyncio.run(_test())