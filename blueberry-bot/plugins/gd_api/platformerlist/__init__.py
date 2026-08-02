from pathlib import Path
import sys
from typing import Any, get_type_hints, override
import httpx
from pydantic import BaseModel

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.file_based_cache import FileBasedCache
    from plugins.gd_api import run_async
    from plugins.gd_api.models import LevelWithID
else:
    from ..file_based_cache import FileBasedCache
    from .. import run_async
    from ..models import LevelWithID

class Level(LevelWithID):
    name:str
    levelID:int
    author:str
    verifier:str
    verifierTime:float
    position:int
    
    @override
    def get_id(self) -> int:
        return self.levelID
    
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} by {self.author} {self.levelID}"

async def getTPLResponse():
    url="https://gdplatformerlist.com/api/levels"
    headers = {
        "User-Agent": ""
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            req = await client.get(url, headers=headers)
        except httpx.ConnectError:
            return None
    if req.status_code!=200:
        return None
    else:
        return req.json()

CACHE=FileBasedCache(list,getTPLResponse,Path("cache")/"tpl.json",cache_name="TPL Cache")

async def getTPLLevels_async():
    data=await CACHE.getOrUpdate()
    if not data:
        return None
    
    levels_raw=data
    levels:list[Level]=[]
    for l in levels_raw:
        try:
            levels.append(Level().load_dict(l))
        except:
            pass
    if not levels:
        return None
    return levels

def getTPLLevels():
    return run_async(getTPLLevels_async())

if __name__ == "__main__":
    import asyncio
    async def _test():
        print(await getTPLLevels_async())
    asyncio.run(_test())