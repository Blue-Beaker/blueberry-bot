from pathlib import Path
import sys

from enum import Enum
import requests
from cachetools import cached, TTLCache
from nonebot import logger

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.gd.models import BaseLevel, Difficulty, Length, Level, LevelList, PageInfo, PlayerDemonLevels, PlayerIcons, PlayerInfo, PlayerLevels, Song
    from plugins.gd_api.gd.search_args import LevelSearchArgs, LevelSearchType, ListSearchType
    from plugins.gd_api.gd.utils import safeBool, safeInt
else:
    from .models import BaseLevel, Difficulty, Length, Level, LevelList, PageInfo, PlayerDemonLevels, PlayerIcons, PlayerInfo, PlayerLevels, Song
    from .search_args import LevelSearchArgs, LevelSearchType, ListSearchType
    from .utils import safeBool, safeInt

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
    return getList2(search,page,searchType=searchType,**kwargs)[0]

@cached(TTLCache(maxsize=100,ttl=60))
def getList2(search:int|str,page:int=0,searchType:ListSearchType|int=0,**kwargs):
    headers = {
        "User-Agent": ""
    }

    data = {
        "str": str(search),
        "type": searchType.value if isinstance(searchType,Enum) else searchType,
        "page": page,
        "secret": "Wmfd2893gb7",
    }
    data.update(kwargs)

    url = "http://www.boomlings.com/database/getGJLevelLists.php"

    logger.info(f"Searching list {search}...")
    req = requests.post(url=url, data=data, headers=headers, timeout=30)
    logger.debug(f"Raw response: {req.text}")
    
    result:list[LevelList]=[]
    spl=req.text.split("#")
    if spl.__len__()<4:
        return [],None
    rawLists=spl[0]
    rawCreators=spl[1]
    rawPageInfo=spl[2]
    rawHashes=spl[3]
    
    for data in parseLine(rawLists):
        l=LevelList().load(data)
        if l.id==-1:
            continue
        result.append(l)
        
    return result,PageInfo().parse(rawPageInfo)

def getLevel(search:int|str|None=None,page:int=0,rated:bool=False,searchType:LevelSearchType|int=0,**kwargs):
    return getLevel2(search,page,rated,searchType=searchType,**kwargs)[0]

@cached(TTLCache(maxsize=100,ttl=60))
def getLevel2(search:int|str|None=None,page:int=0,rated:bool=False,searchType:LevelSearchType|int=0,**kwargs):
    headers = {
    "User-Agent": ""
    }
    
    data = {
        "star": 0 if not rated else 1,
        "type": searchType.value if isinstance(searchType,Enum) else searchType,
        "page": page,
        "secret": "Wmfd2893gb7",
    }
    if search is not None:
        data["str"]=str(search)
    data.update(kwargs)

    url = "http://www.boomlings.com/database/getGJLevels21.php"

    logger.info(f"Searching level {search}...")
    req = requests.post(url=url, data=data, headers=headers, timeout=30)
    logger.debug(f"Raw response: {req.text}")
    
    result:list[Level]=[]
    spl=req.text.split("#")
    if spl.__len__()<5:
        return None,None
    
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
        
    return result,PageInfo().parse(rawPageInfo)


def getLevelSearch(args: LevelSearchArgs):
    return getLevelSearch2(args)[0]

def getLevelSearch2(args: LevelSearchArgs):
    """使用 LevelSearchArgs 链式构造器搜索关卡。

    基于 getLevel2 实现，用 args.getData() 构建请求参数。
    """
    data = args.getData()
    search = data.pop("str", None)
    return getLevel2(search=search, **data)


def getLevelsFromList(listID: int):
    return getLevel(str(listID), searchType=LevelSearchType.LEVEL_FROM_LIST)


def downloadLevel(levelID:int, **kwargs):
    """下载关卡完整数据（含关卡字符串）。

    简写封装，直接返回 Level 对象或 None。
    """
    return downloadLevel2(levelID, **kwargs)

@cached(TTLCache(maxsize=100, ttl=180))
def downloadLevel2(levelID:int, **kwargs):
    """下载关卡完整数据（含关卡字符串）。

    对应端点 downloadGJLevel22.php，返回的响应包含关卡数据字符串（key 4）。
    使用 -1 作为 levelID 可获取每日关卡，-2 获取每周关卡。

    Args:
        levelID: 关卡 ID。使用 -1 获取每日关卡，-2 获取每周关卡。
        **kwargs: 传递给端点的额外参数（如 accountID, gjp, udid 等）。

    Returns:
        Level 对象（含 level_string），若解析失败则返回 None。
    """
    headers = {
        "User-Agent": ""
    }

    data = {
        "levelID": levelID,
        "secret": "Wmfd2893gb7",
    }
    data.update(kwargs)

    url = "http://www.boomlings.com/database/downloadGJLevel22.php"

    logger.info(f"Downloading level {levelID}...")
    req = requests.post(url=url, data=data, headers=headers, timeout=30)
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


@cached(TTLCache(maxsize=100,ttl=60))
def getUser(search:int|str):
    headers = {
        "User-Agent": ""  # Empty User-Agent
    }
    userid=safeInt(search)
    data = {
        "secret": "Wmfd2893gb7"
    }
    player_info=PlayerInfo()
    # Name search
    if True:
        data2=data.copy()
        data2["str"]=str(search)
        req = requests.post('http://www.boomlings.com/database/getGJUsers20.php', data=data2, headers=headers, timeout=30)
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
    req = requests.post("http://www.boomlings.com/database/getGJUserInfo20.php", data=data, headers=headers, timeout=30)
    
    # print(req.text)
    # print(parseDict(req.text))
    
    player_info.load(parseDict(req.text))
    
    return player_info


def getSong(musicID:int):
    headers = {
        "User-Agent": ""  # Empty User-Agent
    }
    data = {
        "secret": "Wmfd2893gb7",
        "songID": musicID
    }

    req = requests.post("http://www.boomlings.com/database/getGJSongInfo.php", data=data, headers=headers)
    if req.status_code!=200:
        return None
    
    result=Song().load(parseDict(req.text,"~|~"))
    return result


# Test code
if __name__ == "__main__":
    # lists=getList(754820)
    # for l in lists:
    #     print(l.name,l.creator,l.levels)
        
    # print(getLevel(lists[0].levels[0]))
    
    # print(getLevel("CATHARSIS",True))
    
    print(getLevel("",rated=True,diff="-2"))
    
    # print(getLevel("645883",rated=True,type=25))
    
    # print(getLevelsFromList(645883))
    
    # print(getLevel(searchType=LevelSearchType.WEEKLY))

    # print(getUser("BlueBeaker"))

    # print(getUser("xioayang"))

    # print(getUser("194268237"))

    # print(getSong(803223))
    # print(getSong(10011122))

    # Test downloadLevel
    
    if False:
        print("\n=== Testing downloadLevel ===")
        level = downloadLevel(126461421)
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
        
    