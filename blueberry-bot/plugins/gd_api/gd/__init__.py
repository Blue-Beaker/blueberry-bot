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
    
class Level(BaseLevel):
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
        
        return f"{diffstr} {self.stars} {'★' if not self.is_plat() else '🌙'}" 
    
    @override
    def load(self,data:dict[str,str]):
        super().load(data)
        self.stars=safeInt(data.get('18'),0)
        self.difficulty=safeInt(data.get('9'),0)//10
        self.length=safeInt(data.get('15'),0)
        self.demon=bool(data.get('17'))
        self.auto=bool(data.get('25'))
        
        return self
    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}, {self.repr_difficulty()}"
    

def parseLine(line:str):
    sublines=line.split("|")
    datas:list[dict[str,str]]=[]
    for subline in sublines:
        spl=subline.split(":")
        data:dict[str,str]={}
        for i in range(0,spl.__len__()-1,2):
            data[spl[i]]=spl[i+1]
        datas.append(data)
    return datas
        
def getList(search:int|str,page:int=0):
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
        return []
    rawLists=spl[0]
    rawCreators=spl[1]
    rawPageInfo=spl[2]
    rawHashes=spl[3]
    
    for data in parseLine(rawLists):
        l=LevelList().load(data)
        if l.id==-1:
            continue
        result.append(l)
        
    return result

def getLevel(search:int|str,page:int=0,rated:bool=False):
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
        return None
    
    rawLevels=spl[0]
    rawCreators=spl[1]
    rawSongs=spl[2]
    rawPageInfo=spl[3]
    rawHashes=spl[4]
    
    for data in parseLine(spl[0]):
        l=Level().load(data)
        if l.id==-1:
            continue
        result.append(l)
    
    creators=spl[1].split("|")
    for i in range(creators.__len__()):
        try:
            creator=creators[i].split(":")[1]
            # print(creator)
            result[i].creator=creator
        except:
            pass
        
    return result


_A = TypeVar(name="_A")
def safeInt(i:Any,fallback:_A=-1) -> int|_A:
    try:
        return int(i)
    except:
        return fallback
    
# Test code
if __name__ == "__main__":
    lists=getList(754820)
    for l in lists:
        print(l.name,l.creator,l.levels)
        
    print(getLevel(lists[0].levels[0]))
    