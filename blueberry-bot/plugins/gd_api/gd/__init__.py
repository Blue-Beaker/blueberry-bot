import requests
from cachetools import cached, TTLCache
from nonebot import logger
    
class Level:
    id:int
    name:str
    creator:str
    def __init__(self) -> None:
        self.levels:list[int]=[]
    @classmethod
    def build(cls,data:dict[str,str]):
        inst=cls()
        inst.id=int(data.get('1','-1'))
        inst.name=data.get('2','')
        inst.creator=data.get('50','')
        list_levels=data.get('51','')
        inst.levels=[int(l) for l in list_levels.split(',') if l]
        return inst
    
    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}, levels={self.levels}"

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
        
# @cached(cache=TTLCache(maxsize=20,ttl=600))
def getList(search:int|str):
    headers = {
        "User-Agent": ""
    }

    data = {
        "str": str(search),
        "type": 0,
        "secret": "Wmfd2893gb7",
    }

    url = "http://www.boomlings.com/database/getGJLevelLists.php"

    logger.info(f"Searching list {search}...")
    req = requests.post(url=url, data=data, headers=headers)
    logger.debug(f"Raw response: {req.text}")
    
    result:list[Level]=[]
    for data in parseLine(req.text):
        l=Level.build(data)
        if l.id==-1:
            continue
        result.append(l)
        
    return result

# @cached(cache=TTLCache(maxsize=20,ttl=600))
def getLevel(search:int|str):
    headers = {
    "User-Agent": ""
    }

    data = {
        "str": str(search),
        "star": 0,
        "type": 0,
        "secret": "Wmfd2893gb7",
    }

    url = "http://www.boomlings.com/database/getGJLevels21.php"

    logger.info(f"Searching level {search}...")
    req = requests.post(url=url, data=data, headers=headers)
    logger.debug(f"Raw response: {req.text}")
    
    result:list[Level]=[]
    spl=req.text.split("#")
    if spl.__len__()<2:
        return None
    
    for data in parseLine(spl[0]):
        l=Level.build(data)
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

# Test code
if __name__ == "__main__":
    lists=getList(754820)
    for l in lists:
        print(l.name,l.creator,l.levels)
        
    print(getLevel(lists[0].levels[0]))
    