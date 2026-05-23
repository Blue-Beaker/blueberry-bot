from enum import Enum
from typing import Any, TypeVar, override
import requests
from cachetools import cached, TTLCache
from nonebot import logger
    
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
    acc_glow:int
    acc_swing:int
    acc_jetpack:int
    def __repr__(self) -> str:
        return f"Icon: {self.__dict__}"
    
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
    
    def load(self,data:dict[str,str]):
        self.user_name=data.get("1","")
        self.user_id=safeInt(data.get("2"))
        self.stars=safeInt(data.get("3"),0)
        self.demons=safeInt(data.get("4"),0)
        self.creator_points=safeInt(data.get("8"),0)
        self.secret_coins=safeInt(data.get("13"),0)
        self.account_id=safeInt(data.get("16"),0)
        self.user_coins=safeInt(data.get("17"),0)
        self.global_rank=safeInt(data.get("30"),-1)
        self.diamonds=safeInt(data.get("46"),0)
        self.mod_level=safeInt(data.get("49"),0)
        self.moons=safeInt(data.get("52"),0)
        
        # Parse icon data
        icon=PlayerIcons()
        icon.color=safeInt(data.get("10"),0)
        icon.color2=safeInt(data.get("11"),0)
        icon.icon_type=safeInt(data.get("14"),0)
        icon.acc_icon=safeInt(data.get("21"),0)
        icon.acc_ship=safeInt(data.get("22"),0)
        icon.acc_ball=safeInt(data.get("23"),0)
        icon.acc_ufo=safeInt(data.get("24"),0)
        icon.acc_wave=safeInt(data.get("25"),0)
        icon.acc_robot=safeInt(data.get("26"),0)
        icon.acc_glow=safeInt(data.get("28"),0)
        icon.acc_swing=safeInt(data.get("53"),0)
        icon.acc_jetpack=safeInt(data.get("54"),0)
        self.icon=icon
        
        # Parse level breakdowns
        classic_raw=data.get("56","")
        if classic_raw:
            self.classic_levels=PlayerLevels().load(classic_raw)
        else:
            self.classic_levels=PlayerLevels()
            
        plat_raw=data.get("57","")
        if plat_raw:
            self.plat_levels=PlayerLevels().load(plat_raw)
        else:
            self.plat_levels=PlayerLevels()
        
        # Demons breakdown (key 55): {easy},{medium},{hard},{insane},{extreme},{easyPlat},{mediumPlat},{hardPlat},{insanePlat},{extremePlat},{weekly},{gauntlet}
        demons_raw=data.get("55","")
        if demons_raw:
            self.classic_demons=PlayerDemonLevels().load(demons_raw)
            spl=demons_raw.split(",")
            if spl.__len__()>=10:
                plat_demons_data=",".join(spl[5:10])
                self.plat_demons=PlayerDemonLevels().load(plat_demons_data)
        else:
            self.classic_demons=PlayerDemonLevels()
            self.plat_demons=PlayerDemonLevels()
        
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

def getList(search:int|str,page:int=0):
    return getList2(search,page)[0]
    
def getList2(search:int|str,page:int=0):
    headers = {
        "User-Agent": ""
    }

    data = {
        "str": str(search),
        "type": 0,
        "page": page,
        "secret": "Wmfd2893gb7",
    }

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

def getLevel(search:int|str,page:int=0,rated:bool=False):
    return getLevel2(search,page,rated)[0]
def getLevel2(search:int|str,page:int=0,rated:bool=False):
    headers = {
    "User-Agent": ""
    }
    
    data = {
        "str": str(search),
        "star": 0 if not rated else 1,
        "type": 0,
        "page": page,
        "secret": "Wmfd2893gb7",
    }

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
        spl=req.text.split("#")
        if spl.__len__()<2:
            return None
        user=spl[0]
        pages=spl[1]
        player_info.load(parseDict(user))
        userid=player_info.account_id
        
    data["targetAccountID"]=str(userid)
    req = requests.post("http://www.boomlings.com/database/getGJUserInfo20.php", data=data, headers=headers)
    
    # print(req.text)
    
    return player_info.load(parseDict(req.text))


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
    
    print(getLevel("CATHARSIS",True))
    
    # user=getUser("BlueBeaker")
    # print(user)
    