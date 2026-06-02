from pathlib import Path
from typing import Any
import requests
from cachetools import cached, TTLCache
from ..file_based_cache import FileBasedCache

class Level:
    name:str
    level_id:int
    creator:str
    def to_dict(self) -> dict:
        return self.__dict__
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.__dict__.update(data)
        return inst
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} by {self.creator} {self.level_id}"

class EmptyResult(Exception):
    pass

def getPemonlistResponse():
    url="https://pemonlist.com/api/list?version=3&page=1&limit=5000"
    headers = {
        "User-Agent": ""
    }
    
    req = requests.get(url, headers=headers)
    if req.status_code!=200:
        return None
    else:
        return req.json()
    
CACHE=FileBasedCache(dict,getPemonlistResponse,Path("cache")/"pemonlist.json")

def getPemonlistLevels():
    # url="https://pemonlist.com/api/list?version=3&page=1&limit=5000"
    # headers = {
    #     "User-Agent": ""
    # }
    
    # req = requests.get(url, headers=headers)
    # if req.status_code!=200:
    #     raise EmptyResult()
    # data=req.json()
    
    data=CACHE.getOrUpdate()
    if not data:
        return None
    
    levels_raw=data.get("data",[])
    levels:list[Level]=[]
    for l in levels_raw:
        try:
            levels.append(Level().from_dict({level_key: l.get(level_key) for level_key in ["name","level_id","creator"]}))
        except:
            pass
    if not levels:
        return None
    return levels

if __name__ == "__main__":
    print(getPemonlistLevels())