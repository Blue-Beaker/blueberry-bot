import asyncio
from typing import Any, TypeVar
from nonebot import logger
import httpx
from .search_args import GDDLSearchArgs
from .models import GDDLSearchLevel

class GDDLSearchResult:
    total:int
    limit:int
    page:int
    levels:list[dict[str,Any]]
    # levels:list[GDDLSearchLevel]
    def __init__(self) -> None:
        pass
    def load(self,resp:dict):
        self.total=safeInt(resp.get("total"),-1)
        self.limit=safeInt(resp.get("limit"),-1)
        self.page=safeInt(resp.get("page"),-1)
        self.levels=resp.get("data",{})
        # self.levels=[GDDLSearchLevel.from_dict(l) for l in resp.get("data",{})]
        return self
    def __repr__(self) -> str:
        return f"[{self.__class__.__name__}]{self.__dict__}"
    
class GDDLSearchResult2:
    total:int
    limit:int
    page:int
    levels:list[GDDLSearchLevel]
    def __init__(self) -> None:
        pass
    def load(self,resp:dict):
        self.total=safeInt(resp.get("total"),-1)
        self.limit=safeInt(resp.get("limit"),-1)
        self.page=safeInt(resp.get("page"),-1)
        self.levels=[GDDLSearchLevel.from_dict(l) for l in resp.get("data",{})]
        return self
    def __repr__(self) -> str:
        return f"[{self.__class__.__name__}]{self.__dict__}"
    
async def searchGDDLLevel(args:GDDLSearchArgs):
    url=f"https://gdladder.com/api/levels"
    headers = {
        "User-Agent": "",
        "accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers, params=args.getData())
        except httpx.ConnectError:
            return None
    if resp.status_code!=200:
        return None
    else:
        return GDDLSearchResult2().load(resp.json())

async def getGDDLResponse(page:int=0,limit:int=25):
    url=f"https://gdladder.com/api/levels?limit={limit}&page={page}&sort=ID&sortDirection=asc&length=6"
    headers = {
        "User-Agent": "",
        "accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.ConnectError:
            return None
    if resp.status_code!=200:
        return None
    else:
        return GDDLSearchResult().load(resp.json())
    
async def fetch_gddl_all_plat():
    levels:list[dict[str,Any]]=[]
    page=0
    total=0
    limit=25
    logger.info(f"Loading levels from GDDL...")
    
    while True:
        
        result=None
        for i in range(0,10):
            result=await getGDDLResponse(page=page,limit=limit)
            if result:
                break
            
            retry_delay=i*5
            logger.info(f"GDDL Page {page} loading failed ({i+1}/10), retrying in {retry_delay} secs...")
            await asyncio.sleep(retry_delay)
            
        if not result:
            return None
        
        total=result.total
        levels.extend(result.levels)
        
        logger.info(f"Loaded GDDL Page {page} ({page*limit+1}-{page*limit+result.levels.__len__()} of {total})")
        
        
        page=page+1
        if page*limit>total:
            break
    
    return levels

_A = TypeVar(name="_A")
def safeInt(i:Any,fallback:_A=-1) -> int|_A:
    try:
        return int(i)
    except:
        return fallback
    
_A = TypeVar(name="_A")
def safeFloat(i:Any,fallback:_A=-1) -> float|_A:
    try:
        return float(i)
    except:
        return fallback

if __name__ == "__main__":
    async def _test():
        resp=await getGDDLResponse()
        if resp:
            for i in resp.levels:
                print(f"{i.get("ID")}: {i.get("Meta",{}).get("Name","")}")
    asyncio.run(_test())
        
        
