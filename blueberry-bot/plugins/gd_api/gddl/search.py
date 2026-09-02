import asyncio
from typing import Any, Callable, TypeVar
from nonebot import logger
import httpx
from .search_args import GDDLSearchArgs
from .models import GDDLSearchLevel,GDDLLevel

class GDDLSearchResult2:
    total:int
    limit:int
    page:int
    levels:list[GDDLSearchLevel]
    def __init__(self) -> None:
        pass
    def load(self,resp:dict):
        self.total=callOrFallback(resp.get("total"),int,-1)
        self.limit=callOrFallback(resp.get("limit"),int,-1)
        self.page=callOrFallback(resp.get("page"),int,-1)
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
        except httpx.ConnectError as e:
            return None,str(e)
    if resp.status_code!=200:
        return None,resp.text
    else:
        return GDDLSearchResult2().load(resp.json()),None
    
async def getGDDLLevel(level_id:int):
    url=f"https://gdladder.com/api/levels/{level_id}"
    headers = {
        "User-Agent": "",
        "accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.ConnectError as e:
            return None,str(e)
    if resp.status_code!=200:
        return None,resp.text
    else:
        return GDDLLevel().load(resp.json()),None
    
_A = TypeVar(name="_A")
def callOrFallback(i:Any,callable:Callable[[Any],_A],fallback:_A=-1) -> _A:
    try:
        return callable(i)
    except:
        return fallback