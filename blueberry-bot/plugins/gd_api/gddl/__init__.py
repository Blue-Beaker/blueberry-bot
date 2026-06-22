from pathlib import Path
import sys
from gddl_internal import GDDLSearchResult,getGDDLResponse,fetch_gddl_all_untiered,safeFloat,safeInt

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.file_based_cache import FileBasedCache
else:
    from ..file_based_cache import FileBasedCache

class GDDLLevel:
    ID:int=0
    Rating:float|None=None
    Enjoyment:float|None=None
    EnjoymentCount:int=0
    Popularity:float=0
    Length:int=0
    # Meta
    Name:str=""
    Description:str=""
    # Meta/Publisher/name
    Publisher:str=""
    def load(self,data:dict):
        self.ID=safeInt(data.get("ID"),self.ID)
        self.Rating=safeFloat(data.get("Rating"),self.Rating)
        self.Enjoyment=safeFloat(data.get("Enjoyment"),self.Enjoyment)
        self.EnjoymentCount=safeInt(data.get("EnjoymentCount"),self.EnjoymentCount)
        self.Popularity=safeFloat(data.get("Popularity"),self.Popularity)
        self.Length=safeInt(data.get("Length"),self.Length)
        
        meta=data.get("Meta")
        if isinstance(meta,dict):
            self.Name=meta.get("Name","")
            self.Description=meta.get("Description","")
            
        publ=data.get("Publisher")
        if isinstance(publ,dict):
            self.Publisher=publ.get("name","")
            
        return self
    def __repr__(self) -> str:
        return f"GDDLLevel[{self.Name} by {self.Publisher} {self.ID}]"

CACHE=FileBasedCache(list,fetch_gddl_all_untiered,Path("cache")/"gddl_untiered.json",cache_name="GDDL Untiered Cache",expiration=8640000)

def getGDDLUntiered():
    data=CACHE.getOrUpdate()
    if not data:
        return None
    levels:dict[int,GDDLLevel]={}
    for l in data:
        level=GDDLLevel().load(l)
        levels[level.ID]=level
    return levels
    
if __name__ == "__main__":
    print(getGDDLUntiered())