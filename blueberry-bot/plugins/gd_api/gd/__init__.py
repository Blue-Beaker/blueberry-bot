from enum import Enum
from typing import Any, TypeVar, override
import requests
from cachetools import cached, TTLCache
from nonebot import logger

class ListSearchType(Enum):
    SEARCH=0
    DOWNLOADS=1
    LIKES=2
    TRENDING=3
    RECENT=4
    FROM_USER=5
    LISTS_BUTTON=6
    MAGIC=7 #(returns the same levels as most liked)
    AWARDED=11
    FOLLOWED=12
    FRIENDS=13
    SENT=27

class LevelSearchType(Enum):
    SEARCH=0
    DOWNLOADS=1
    LIKES=2
    TRENDING=3
    RECENT=4
    FROM_USER=5
    FEATURED=6
    MAGIC=7
    MOD_SENT=8
    LIST_OF_LEVELS=10
    AWARDED=11
    FOLLOWED=12
    FRIENDS=13
    WORLD_LIKED=15
    HALL_OF_FAME=16
    WORLD_FEATURED=17
    DAILY=21
    WEEKLY=22
    LEVEL_FROM_LIST=25
    SENT=27
    
class BaseLevel:
    id:int
    name:str
    creator:str
    def __init__(self) -> None:
        pass
    def load(self,data:dict[str,str]):
        self.id=int(data.get('1','-1'))
        self.name=data.get('2','')
        self.creator=data.get('50','')
        return self
    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}"
    
class LevelList(BaseLevel):
    def __init__(self) -> None:
        self.levels:list[int]=[]
    @override
    def load(self,data:dict[str,str]):
        super().load(data)
        list_levels=data.get('51','')
        self.levels=[int(l) for l in list_levels.split(',') if l]
        return self
    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}, levels={self.levels}"

class Length(Enum):
    TINY=0
    SHORT=1
    MEDIUM=2
    LONG=3
    XL=4
    PLAT=5
    
class Difficulty(Enum):
    NA=0
    EASY=1
    NORMAL=2
    HARD=3
    HARDER=4
    INSANE=5
    EASY_DEMON=6
    MEDIUM_DEMON=7
    HARD_DEMON=8
    INSANE_DEMON=9
    EXTREME_DEMON=10
    AUTO=11
    
class PageInfo:
    def __init__(self) -> None:
        self.total=0
        self.offset=0
        self.amount=10
    def parse(self,line:str):
        spl=line.split(":")
        try:
            if spl.__len__()>=3:
                self.total=int(spl[0])
                self.offset=int(spl[1])
                self.amount=int(spl[2])
        except:
            pass
        return self
    
class Level(BaseLevel):
    creator_id:int
    def __init__(self) -> None:
        self.stars:int=0
        self.difficulty:int=0
        self.length:int=0
        self.demon:bool=False
        self.auto:bool=False
        
    def is_plat(self):
        return self.length==Length.PLAT.value
    def get_difficulty(self):
        if self.auto:
            return Difficulty.AUTO
        if not self.demon:
            return Difficulty(self.difficulty)
        else:
            return Difficulty(self.difficulty+5)
    def repr_difficulty(self):
        diffs=['NA','Easy','Normal','Hard','Harder','Insane','EZD','MED','HDD','INSD','EXD','Auto']
        diffstr=diffs[self.get_difficulty().value]
        if self.demon and self.is_plat():
            diffstr=diffstr.removesuffix('D')+'P'
        
        return f"{diffstr} {self.stars} {'⭐' if not self.is_plat() else '🌙'}" 
    
    @override
    def load(self,data:dict[str,str]):
        super().load(data)
        self.stars=safeInt(data.get('18'),0)
        self.difficulty=safeInt(data.get('9'),0)//10
        self.length=safeInt(data.get('15'),0)
        self.demon=bool(data.get('17'))
        self.auto=bool(data.get('25'))
        self.creator_id=safeInt(data.get('6'))
        
        return self
    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}, {self.repr_difficulty()}"

class PlayerIcons:
    color:int
    color2:int
    icon_type:int
    acc_icon:int
    acc_ship:int
    acc_ball:int
    acc_ufo:int
    acc_wave:int
    acc_robot:int
    glow_on:int
    glow_color:int
    acc_spider:int
    acc_swing:int
    acc_jetpack:int
    def __init__(self) -> None:
        self.color=0
        self.color2=0
        self.icon_type=0
        self.acc_icon=0
        self.acc_ship=0
        self.acc_ball=0
        self.acc_ufo=0
        self.acc_wave=0
        self.acc_robot=0
        self.glow_on=0
        self.glow_color=-1
        self.acc_spider=0
        self.acc_swing=0
        self.acc_jetpack=0
    def __repr__(self) -> str:
        return f"Icon: {self.__dict__}"
    def get_icon_for_type(self,icon_type:str):
        field_name="acc_icon" if icon_type=="cube" else "acc_"+icon_type
        icon_id=getattr(self,field_name,None)
        return icon_id if isinstance(icon_id,int) else None
        
    
class PlayerDemonLevels:
    ezd:int=-1
    med:int=-1
    hdd:int=-1
    insd:int=-1
    exd:int=-1
    
    weekly:int=-1
    gauntlet:int=-1
    
    def load(self,data:str):
        spl=data.split(",")
        if spl.__len__()>=5:
            self.ezd=safeInt(spl[0])
            self.med=safeInt(spl[1])
            self.hdd=safeInt(spl[2])
            self.insd=safeInt(spl[3])
            self.exd=safeInt(spl[4])
        if spl.__len__()>=12:
            self.weekly=safeInt(spl[10])
            self.gauntlet=safeInt(spl[11])
        return self
    
    def sum(self):
        l=self
        return l.ezd+l.med+l.hdd+l.insd+l.exd
    
    def __repr__(self) -> str:
        return f"Demons: {self.__dict__}"

class PlayerLevels:
    auto:int=-1
    easy:int=-1
    normal:int=-1
    hard:int=-1
    harder:int=-1
    insane:int=-1
    
    daily:int=-1
    gauntlet:int=-1
    
    def load(self,data:str):
        spl=data.split(",")
        if spl.__len__()>=7:
            self.auto=safeInt(spl[0])
            self.easy=safeInt(spl[1])
            self.normal=safeInt(spl[2])
            self.hard=safeInt(spl[3])
            self.harder=safeInt(spl[4])
            self.insane=safeInt(spl[5])
            self.daily=safeInt(spl[6])
            self.gauntlet=safeInt(spl[7]) if spl.__len__()>7 else -1
        return self
    
    def sum(self):
        l=self
        return l.auto+l.easy+l.normal+l.hard+l.harder+l.insane
    
    def __repr__(self) -> str:
        return f"Levels: {self.__dict__}"
    
class PlayerInfo:
    user_name:str
    user_id:int
    stars:int
    moons:int
    demons:int
    diamonds:int
    mod_level:int
    
    global_rank:int
    creator_points:int
    secret_coins:int
    account_id:int
    user_coins:int
    
    icon:PlayerIcons
    classic_levels:PlayerLevels
    plat_levels:PlayerLevels
    classic_demons:PlayerDemonLevels
    plat_demons:PlayerDemonLevels
    
    def __init__(self) -> None:
        self.user_name=""
        self.user_id=0
        self.stars=0
        self.moons=0
        self.demons=0
        self.diamonds=0
        self.mod_level=0
        self.global_rank=-1
        self.creator_points=0
        self.secret_coins=0
        self.account_id=0
        self.user_coins=0
        self.icon=PlayerIcons()
        self.classic_levels=PlayerLevels()
        self.plat_levels=PlayerLevels()
        self.classic_demons=PlayerDemonLevels()
        self.plat_demons=PlayerDemonLevels()
    
    def load(self,data:dict[str,str]):
        self.user_name = data.get("1", self.user_name)
        self.user_id = safeInt(data.get("2"), self.user_id)
        self.stars = safeInt(data.get("3"), self.stars)
        self.demons = safeInt(data.get("4"), self.demons)
        self.creator_points = safeInt(data.get("8"), self.creator_points)
        self.secret_coins = safeInt(data.get("13"), self.secret_coins)
        self.account_id = safeInt(data.get("16"), self.account_id)
        self.user_coins = safeInt(data.get("17"), self.user_coins)
        self.global_rank = safeInt(data.get("30"), self.global_rank)
        self.diamonds = safeInt(data.get("46"), self.diamonds)
        self.mod_level = safeInt(data.get("49"), self.mod_level)
        self.moons = safeInt(data.get("52"), self.moons)
        
        # Parse icon data — only update keys present in data
        icon=self.icon
        icon.color = safeInt(data.get("10"), icon.color)
        icon.color2 = safeInt(data.get("11"), icon.color2)
        icon.icon_type = safeInt(data.get("14"), icon.icon_type)
        icon.acc_icon = safeInt(data.get("21"), icon.acc_icon)
        icon.acc_ship = safeInt(data.get("22"), icon.acc_ship)
        icon.acc_ball = safeInt(data.get("23"), icon.acc_ball)
        icon.acc_ufo = safeInt(data.get("24"), icon.acc_ufo)
        icon.acc_wave = safeInt(data.get("25"), icon.acc_wave)
        icon.acc_robot = safeInt(data.get("26"), icon.acc_robot)
        icon.glow_on = safeInt(data.get("28"), icon.glow_on)
        icon.acc_spider = safeInt(data.get("43"), icon.acc_spider)
        icon.glow_color = safeInt(data.get("51"), icon.glow_color)
        icon.acc_swing = safeInt(data.get("53"), icon.acc_swing)
        icon.acc_jetpack = safeInt(data.get("54"), icon.acc_jetpack)
        
        if not icon.glow_on:
            icon.glow_color=-1
        
        # Parse level breakdowns — only if present
        classic_raw=data.get("56")
        if classic_raw:
            self.classic_levels=PlayerLevels().load(classic_raw)
            
        plat_raw=data.get("57")
        if plat_raw:
            self.plat_levels=PlayerLevels().load(plat_raw)
        
        # Demons breakdown (key 55): {easy},{medium},{hard},{insane},{extreme},{easyPlat},{mediumPlat},{hardPlat},{insanePlat},{extremePlat},{weekly},{gauntlet}
        demons_raw=data.get("55")
        if demons_raw:
            self.classic_demons=PlayerDemonLevels().load(demons_raw)
            spl=demons_raw.split(",")
            if spl.__len__()>=10:
                plat_demons_data=",".join(spl[5:10])
                self.plat_demons=PlayerDemonLevels().load(plat_demons_data)
        
        return self
        
    def __repr__(self) -> str:
        return f"{self.user_name}: {self.__dict__}"


def parseDict(s:str):
    spl=s.split(":")
    data:dict[str,str]={}
    for i in range(0,spl.__len__()-1,2):
        data[spl[i]]=spl[i+1]
    return data
    

def parseLine(line:str):
    sublines=line.split("|")
    datas:list[dict[str,str]]=[]
    for subline in sublines:
        # spl=subline.split(":")
        # data:dict[str,str]={}
        # for i in range(0,spl.__len__()-1,2):
        #     data[spl[i]]=spl[i+1]
        # datas.append(data)
        datas.append(parseDict(subline))
    return datas

def getList(search:int|str,page:int=0,searchType:ListSearchType|int=0,**kwargs):
    return getList2(search,page,searchType=searchType,**kwargs)[0]
    
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
    req = requests.post(url=url, data=data, headers=headers)
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
    req = requests.post(url=url, data=data, headers=headers)
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

def getLevelsFromList(listID:int):
    return getLevel(str(listID),searchType=LevelSearchType.LEVEL_FROM_LIST)

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
    if userid<0:
        data2=data.copy()
        data2["str"]=str(search)
        req = requests.post('http://www.boomlings.com/database/getGJUsers20.php', data=data2, headers=headers)
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
    req = requests.post("http://www.boomlings.com/database/getGJUserInfo20.php", data=data, headers=headers)
    
    # print(req.text)
    # print(parseDict(req.text))
    
    player_info.load(parseDict(req.text))
    
    return player_info


_A = TypeVar(name="_A")
def safeInt(i:Any,fallback:_A=-1) -> int|_A:
    try:
        return int(i)
    except:
        return fallback
    
# Test code
if __name__ == "__main__":
    # lists=getList(754820)
    # for l in lists:
    #     print(l.name,l.creator,l.levels)
        
    # print(getLevel(lists[0].levels[0]))
    
    # print(getLevel("CATHARSIS",True))
    
    # print(getLevel("645883",rated=True,type=25))
    
    # print(getLevelsFromList(645883))
    
    # print(getLevel(searchType=LevelSearchType.WEEKLY))
    
    print(getUser("BlueBeaker"))
    
    print(getUser("xioayang"))
    
    print(getUser("lastcavespider"))
    