from pathlib import Path
import sys
from typing import Any
import requests
from cachetools import cached, TTLCache

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.file_based_cache import FileBasedCache
else:
    from ..file_based_cache import FileBasedCache

class Level:
    level_id:int
    name:str
    publisher_id:str
    position:int
    points:int
    tags:list[str]
    legacy:bool
    
    def to_dict(self) -> dict:
        return self.__dict__
    def load_dict(self,data:dict):
        for level_key in ["level_id","name","position","publisher_id","points","tags","legacy"]:
            self.__dict__[level_key]=data.get(level_key)
        return self
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.load_dict(data)
        return inst
    
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} by {self.publisher_id} {self.level_id}"

def getResp(url:str):
    headers = {
        "User-Agent": "",
        'accept': 'application/json' 
    }
    req = requests.get(url, headers=headers,timeout=30)
    if req.status_code!=200:
        return None
    else:
        return req.json()
def aredlResp():
    return getResp(f"https://api.aredl.net/v2/api/aredl/levels")
def areplResp():
    return getResp(f"https://api.aredl.net/v2/api/arepl/levels")

CACHE_CLASSIC=FileBasedCache(dict,aredlResp,Path("cache")/"aredl_classic.json",cache_name="AREDL_Classic Cache")
CACHE_PLAT=FileBasedCache(dict,areplResp,Path("cache")/"aredl_plat.json",cache_name="AREDL_Plat Cache")

def getAREDLLevels(plat:bool=False):
    if plat:
        data=CACHE_PLAT.getOrUpdate()
    else:
        data=CACHE_CLASSIC.getOrUpdate()
    if not data:
        return None
    
    levels:list[Level]=[]
    for l in data:
        try:
            levels.append(Level().load_dict(l))
        except:
            pass
    if not levels:
        return None
    return levels

if __name__ == "__main__":
    print(getAREDLLevels())
    print(getAREDLLevels(True))