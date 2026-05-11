import requests
from cachetools import cached, TTLCache

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
    
@cached(cache=TTLCache(maxsize=20,ttl=600))
def getPemonlistLevels():
    url="https://pemonlist.com/api/list?version=3&page=1&limit=1000"
    headers = {
        "User-Agent": ""
    }
    
    req = requests.get(url, headers=headers)
    if req.status_code!=200:
        return None
    levels_raw=req.json().get("data",[])
    levels:list[Level]=[]
    for l in levels_raw:
        try:
            levels.append(Level().from_dict({level_key: l.get(level_key) for level_key in ["name","level_id","creator"]}))
        except:
            pass
    return levels
if __name__ == "__main__":
    print(getPemonlistLevels())