from pathlib import Path
import sys

from enum import Enum
import httpx
from cachetools import TTLCache
from cachetools_async import cached as async_cached
from nonebot import logger,get_plugin_config
from pydantic import BaseModel

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.gd.models import BaseLevel, Difficulty, Length, Level, LevelList, PageInfo, PlayerDemonLevels, PlayerIcons, PlayerInfo, PlayerLevels, Song, SearchStatus
    from plugins.gd_api.gd.search_args import LevelSearchArgs, LevelSearchType, ListSearchType
    from plugins.gd_api.gd.utils import safeBool, safeInt
    from plugins.gd_api.gd import run_async
else:
    from .models import BaseLevel, Difficulty, Length, Level, LevelList, PageInfo, PlayerDemonLevels, PlayerIcons, PlayerInfo, PlayerLevels, Song, SearchStatus
    from .search_args import LevelSearchArgs, LevelSearchType, ListSearchType
    from .utils import safeBool, safeInt
    from .. import run_async

class Config(BaseModel):
    gd_endpoint_base:str="https://www.boomlings.com"

GD_ENDPOINT_BASE="https://www.boomlings.com"

try:
    plugin_cfg=get_plugin_config(Config)
except:
    plugin_cfg=Config()
    
GD_ENDPOINT_BASE=plugin_cfg.gd_endpoint_base

# 共享的 httpx AsyncClient
_client: httpx.AsyncClient | None = None

async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30, headers={"User-Agent": ""})
    return _client

async def close_client():
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None

import asyncio

def parseDict(s:str,splitter:str=":"):
    spl=s.split(splitter)
    data:dict[str,str]={}
    for i in range(0,spl.__len__()-1,2):
        data[spl[i]]=spl[i+1]
    return data


def parseLine(line:str,line_spl:str="|",dict_spl:str=":"):
    sublines=line.split(line_spl)
    datas:list[dict[str,str]]=[]
    for subline in sublines:
        # spl=subline.split(":")
        # data:dict[str,str]={}
        # for i in range(0,spl.__len__()-1,2):
        #     data[spl[i]]=spl[i+1]
        # datas.append(data)
        datas.append(parseDict(subline,dict_spl))
    return datas

def getList(search:int|str,page:int=0,searchType:ListSearchType|int=0,**kwargs):
    return run_async(getList_async(search,page,searchType=searchType,**kwargs))

def getList2(search:int|str,page:int=0,searchType:ListSearchType|int=0,**kwargs):
    return run_async(getList2_async(search,page,searchType=searchType,**kwargs))

def getLevel(search:int|str|None=None,page:int=0,rated:bool=False,searchType:LevelSearchType|int=0,**kwargs):
    return run_async(getLevel_async(search,page,rated,searchType=searchType,**kwargs))

def getLevel2(search:int|str|None=None,page:int=0,rated:bool=False,searchType:LevelSearchType|int=0,**kwargs):
    return run_async(getLevel2_async(search,page,rated,searchType=searchType,**kwargs))

def getLevelSearch(args: LevelSearchArgs):
    return run_async(getLevelSearch_async(args))

def getLevelSearch2(args: LevelSearchArgs):
    return run_async(getLevelSearch2_async(args))

def getLevelsFromList(listID: int):
    return run_async(getLevelsFromList_async(listID))

def getLevelsFromUser(args: LevelSearchArgs):
    return run_async(getLevelsFromUser_async(args))


# ---- Async 核心实现 ----

async def getList_async(search:int|str,page:int=0,searchType:ListSearchType|int=0,**kwargs):
    result, _ = await getList2_async(search, page, searchType=searchType, **kwargs)
    return result

@async_cached(TTLCache(maxsize=100, ttl=60))  # type: ignore[arg-type]
async def getList2_async(search:int|str,page:int=0,searchType:ListSearchType|int=0,**kwargs):
    client = await get_client()

    data = {
        "str": str(search),
        "type": searchType.value if isinstance(searchType,Enum) else searchType,
        "page": page,
        "secret": "Wmfd2893gb7",
    }
    data.update(kwargs)

    url = GD_ENDPOINT_BASE+"/database/getGJLevelLists.php"

    logger.info(f"Searching list {search}...")
    try:
        req = await client.post(url=url, data=data)
    except httpx.NetworkError as e:
        logger.error(f"Error fetching list: {e}")
        return [],PageInfo().setStatus(SearchStatus.NETWORK_ERROR)
        
    logger.debug(f"Raw response: {req.text}")
    
    result:list[LevelList]=[]
    
    if req.text=='-1':
        return result,PageInfo().setStatus(SearchStatus.EMPTY_RESULTS)
    
    spl=req.text.split("#")
    if spl.__len__()<4:
        logger.error(f"Parse Failed: {req.text}")
        return [],PageInfo().setStatus(SearchStatus.PARSE_FAILED)
    rawLists=spl[0]
    rawCreators=spl[1]
    rawPageInfo=spl[2]
    rawHashes=spl[3]
    
    for data in parseLine(rawLists):
        l=LevelList().load(data)
        if l.id==-1:
            continue
        result.append(l)
        
    logger.info(f"Found {result.__len__()} results.")
    return result,PageInfo().parse(rawPageInfo)

async def getLevel_async(search:int|str|None=None,page:int=0,rated:bool=False,searchType:LevelSearchType|int=0,**kwargs):
    result, _ = await getLevel2_async(search, page, rated, searchType=searchType, **kwargs)
    return result

@async_cached(TTLCache(maxsize=100, ttl=60))  # type: ignore[arg-type]
async def getLevel2_async(search:int|str|None=None,page:int=0,rated:bool=False,searchType:LevelSearchType|int=0,**kwargs):
    client = await get_client()
    
    data = {
        "star": 0 if not rated else 1,
        "type": searchType.value if isinstance(searchType,Enum) else searchType,
        "page": page,
        "secret": "Wmfd2893gb7",
    }
    if search is not None:
        data["str"]=str(search)
    data.update(kwargs)

    url = GD_ENDPOINT_BASE+"/database/getGJLevels21.php"

    logger.info(f"Searching level {search}...")
    try:
        req = await client.post(url=url, data=data)
    except httpx.NetworkError as e:
        logger.error(f"Error fetching level: {e}")
        return None,PageInfo().setStatus(SearchStatus.NETWORK_ERROR)
    logger.debug(f"Raw response: {req.text}")
    
    
    result:list[Level]=[]
    
    if req.text=='-1':
        logger.error(f"No results: {req.text}")
        return result,PageInfo().setStatus(SearchStatus.EMPTY_RESULTS)
        
    spl=req.text.split("#")
    if spl.__len__()<5:
        logger.error(f"Parse Failed: {req.text}")
        return None,PageInfo().setStatus(SearchStatus.PARSE_FAILED)
    
    rawLevels=spl[0]
    rawCreators=spl[1]
    rawSongs=spl[2]
    rawPageInfo=spl[3]
    rawHashes=spl[4]
    
    leveldata=parseLine(spl[0])
    
    creator_to_level:dict[int,Level]={}
    
    for data in leveldata:
        l=Level().load(data)
        if l.id==-1:
            continue
        result.append(l)
        creator_to_level[l.creator_id]=l
    
    creators=spl[1].split("|")
    for c in creators:
        try:
            spl=c.split(":")
            creator_id=safeInt(spl[0])
            creator=spl[1]
            # print(creator)
            level=creator_to_level.get(creator_id)
            if level:
                level.creator=creator
        except:
            pass
        
    logger.info(f"Found {result.__len__()} results.")
    return result,PageInfo().parse(rawPageInfo)


async def getLevelSearch_async(args: LevelSearchArgs):
    result, _ = await getLevelSearch2_async(args)
    return result

async def getLevelSearch2_async(args: LevelSearchArgs):
    """使用 LevelSearchArgs 链式构造器搜索关卡。

    基于 getLevel2_async 实现，用 args.getData() 构建请求参数。
    """
    data = args.getData()
    search = data.pop("str", None)
    return await getLevel2_async(search=search, **data)  # type: ignore[arg-type]


async def getLevelsFromList_async(listID: int):
    return await getLevel_async(str(listID), searchType=LevelSearchType.LEVEL_FROM_LIST)

async def getLevelsFromUser_async(args: LevelSearchArgs):
    args.setSearchType(LevelSearchType.FROM_USER)
    if not args.getSearch():
        return None,PageInfo().setStatus(SearchStatus.NO_USER_ARG)
    user=await getUser_async(args.getSearch() or "")
    if not user or not user.user_id:
        return None,PageInfo().setStatus(SearchStatus.USER_NOT_FOUND)
    args.setSearch(str(user.user_id))
    
    return await getLevelSearch2_async(args)


def downloadLevel(levelID:int, **kwargs):
    """下载关卡完整数据（含关卡字符串）。

    简写封装，直接返回 Level 对象或 None。
    """
    return run_async(downloadLevel_async(levelID, **kwargs))

def downloadLevel2(levelID:int, **kwargs):
    return run_async(downloadLevel2_async(levelID, **kwargs))

def getUser(search:int|str):
    return run_async(getUser_async(search))

def getSong(musicID:int):
    return run_async(getSong_async(musicID))


# ---- Async 核心实现（续） ----

async def downloadLevel_async(levelID:int, **kwargs):
    """下载关卡完整数据（含关卡字符串），async 版本。"""
    return await downloadLevel2_async(levelID, **kwargs)

@async_cached(TTLCache(maxsize=100, ttl=180))  # type: ignore[arg-type]
async def downloadLevel2_async(levelID:int, **kwargs):
    """下载关卡完整数据（含关卡字符串），async 版本。

    对应端点 downloadGJLevel22.php，返回的响应包含关卡数据字符串（key 4）。
    使用 -1 作为 levelID 可获取每日关卡，-2 获取每周关卡。

    Args:
        levelID: 关卡 ID。使用 -1 获取每日关卡，-2 获取每周关卡。
        **kwargs: 传递给端点的额外参数（如 accountID, gjp, udid 等）。

    Returns:
        Level 对象（含 level_string），若解析失败则返回 None。
    """
    client = await get_client()

    data = {
        "levelID": levelID,
        "secret": "Wmfd2893gb7",
    }
    data.update(kwargs)

    url = GD_ENDPOINT_BASE+"/database/downloadGJLevel22.php"

    logger.info(f"Downloading level {levelID}...")
    req = await client.post(url=url, data=data)
    logger.debug(f"Raw response: {req.text}")

    spl = req.text.split("#")
    if spl.__len__() < 3:
        return None

    rawLevel = spl[0]

    level_data = parseDict(rawLevel)
    level = Level().load(level_data)
    if level.id == -1:
        return None

    return level

@async_cached(TTLCache(maxsize=100, ttl=60))  # type: ignore[arg-type]
async def getUser_async(search:int|str):
    client = await get_client()
    userid=safeInt(search)
    data = {
        "secret": "Wmfd2893gb7"
    }
    player_info=PlayerInfo()
    # Name search
    
    data2=data.copy()
    data2["str"]=str(search)
    
    logger.info(f"Finding User {search}...")
    req = await client.post(GD_ENDPOINT_BASE+"/database/getGJUsers20.php", data=data2)
    # logger.debug(f"getGJUsers20.php raw response: {req.text}")
    spl=req.text.split("#")
    if spl.__len__()<2:
        return None
    user=spl[0]
    pages=spl[1]
    # logger.debug(f"getGJUsers20.php parsed user dict: {parseDict(user)}")
    player_info.load(parseDict(user))
    userid=player_info.account_id
        
    data["targetAccountID"]=str(userid)
    
    # logger.info(f"Getting user info for {search}...")
    req = await client.post(GD_ENDPOINT_BASE+"/database/getGJUserInfo20.php", data=data)
    
    # print(req.text)
    # print(parseDict(req.text))
    
    player_info.load(parseDict(req.text))
    
    logger.info(f"Got user: name={player_info.user_name} uid={player_info.user_id} accid={player_info.account_id}")
    return player_info


async def getSong_async(musicID:int):
    client = await get_client()
    data = {
        "secret": "Wmfd2893gb7",
        "songID": musicID
    }

    logger.info(f"Finding Song {musicID}...")
    try:
        req = await client.post(GD_ENDPOINT_BASE+"/database/getGJSongInfo.php", data=data)
    except httpx.NetworkError as e:
        logger.error(f"Error fetching song: {e}")
        return None
    if req.status_code!=200:
        return None
    
    result=Song().load(parseDict(req.text,"~|~"))
    
    logger.info(f"Got song {musicID}: {result.name} by {result.artistID}")
    return result


# Test code
if __name__ == "__main__":
    async def _test():
        # lists=await getList_async(754820)
        # for l in lists:
        #     print(l.name,l.creator,l.levels)
            
        # print(await getLevel_async(lists[0].levels[0]))
        
        # print(await getLevel_async("CATHARSIS",True))
        
        print(await getLevel_async("",rated=True,diff="-2"))
        
        # print(await getLevel_async("645883",rated=True,type=25))
        
        # print(await getLevelsFromList_async(645883))
        
        # print(await getLevel_async(searchType=LevelSearchType.WEEKLY))
        
        # print(await getUser_async("BlueBeaker"))
        
        # print(await getUser_async("xioayang"))
        
        # print(await getUser_async("194268237"))
        
        # print(await getSong_async(803223))
        # print(await getSong_async(10011122))
        
        # Test downloadLevel
        
        if False:
            print("\n=== Testing downloadLevel ===")
            level = await downloadLevel_async(126461421)
            print(f"Level: {level}")
            if level:
                print(f"  description: {level.get_description()}")
                print(f"  version: {level.version}")
                print(f"  game_version: {level.game_version}")
                print(f"  objects: {level.objects}")
                print(f"  has level_string: {bool(level.level_string)}")
                print(f"  level_string length: {len(level.level_string) if level.level_string else 0}")
                print(f"  password: {level.password}")
                print(f"  upload_date: {level.upload_date}")
                print(f"  update_date: {level.update_date}")
                print(f"  song_ids: {level.song_ids}")
                print(f"  sfx_ids: {level.sfx_ids}")
                print(f"  verification_time: {level.verification_time}")
    asyncio.run(_test())
        
    