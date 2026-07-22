import os
from pathlib import Path
import sys
from nonebot import logger
import httpx
from cachetools import TTLCache
from cachetools_async import cached as async_cached

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api import run_async
else:
    from .. import run_async

def getThumbnail(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/",small:bool=False):
    return run_async(getThumbnail_async(levelID,api_base,small))

@async_cached(TTLCache(maxsize=20, ttl=600))  # type: ignore[arg-type]
async def getThumbnail_async(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/",small:bool=False):
    url=getThumbnailUrl(levelID,api_base,small)
    logger.info(f"Getting thumbnail for {levelID}: {url}")
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": ""}) as client:
        req = await client.get(url=url)
    if req.status_code!=200:
        return None
    return req.content

def getThumbnailUrl(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/",small:bool=False):
    url=api_base+str(levelID)
    if small:
        url=url+"/small"
    return url

        
if __name__ == "__main__":
    import asyncio
    os.makedirs("gdguess_data/images",exist_ok=True)
    async def _test():
        img=await getThumbnail_async(127917376)
        if img:
            with open(f"gdguess_data/images/{127917376}.webp","wb") as f:
                f.write(img)
    asyncio.run(_test())