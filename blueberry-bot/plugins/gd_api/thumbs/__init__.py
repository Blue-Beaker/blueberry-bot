import os
from nonebot import logger
import httpx
from cachetools import TTLCache
from cachetools_async import cached as async_cached

from .. import run_async

def getThumbnail(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/",small:bool=False):
    return run_async(getThumbnail_async(levelID,api_base,small))

@async_cached(TTLCache(maxsize=20, ttl=60))  # type: ignore[arg-type]
async def getThumbnailRaw(url:str):
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": ""}) as client:
        req = await client.get(url=url)
        req.raise_for_status()
    return req

async def getThumbnail_async(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/",small:bool=False):
    url=getThumbnailUrl(levelID,api_base,small)
    logger.info(f"Getting thumbnail for {levelID}: {url}")
    try:
        req = await getThumbnailRaw(url=url)
    except httpx.HTTPError as e:
        logger.error(f"Error getting thumbnail for {levelID}: {e}")
        return None
    return req.content

def getThumbnailUrl(levelID:int,api_base:str="https://levelthumbs.prevter.me/thumbnail/",small:bool=False):
    url=api_base+str(levelID)
    if small:
        url=url+"/small"
    return url
