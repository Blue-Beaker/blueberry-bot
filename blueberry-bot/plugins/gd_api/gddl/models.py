from abc import abstractmethod
from enum import Enum
from typing import Any, get_type_hints

from ..models import BaseAdaptingModel

class GDDLDifficulty(Enum):
    OFFICIAL="Official"
    EASY="Easy"
    MEDIUM="Medium"
    HARD="Hard"
    INSANE="Insane"
    EXTREME="Extreme"

class GDDLSearchLevel(BaseAdaptingModel):
    id: int=0
    rating: float=0
    enjoyment: float=0
    showcase: str=""
    name: str=""
    difficulty: GDDLDifficulty=GDDLDifficulty.OFFICIAL
    rarity: int=0
    publisherName: str=""
    songName: str=""
    isInPack: int=0
    isComplete: int=0
    def to_gddl_level(self):
        return GDDLLevel.from_search(self)
    def __repr__(self) -> str:
        return f"GDDLSearchLevel[{self.name} by {self.publisherName} {self.id}]"
    
class GDDLLevel(BaseAdaptingModel):
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
    @classmethod
    def from_search(cls,data:GDDLSearchLevel):
        inst=cls()
        inst.ID=data.id
        inst.Name=data.name
        inst.Rating=data.rating
        inst.Enjoyment=data.enjoyment
        inst.Publisher=data.publisherName
        return inst
    def load(self,data:dict):
        for k in ["ID","Rating","Enjoyment","EnjoymentCount","Popularity","Length"]:
            if k in data.keys():
                self.adapt_variable(k,data[k])
        
        # self.ID=int(data.get("ID"),self.ID)
        # self.Rating=float(data.get("Rating"),self.Rating)
        # self.Enjoyment=float(data.get("Enjoyment"),self.Enjoyment)
        # self.EnjoymentCount=int(data.get("EnjoymentCount"),self.EnjoymentCount)
        # self.Popularity=float(data.get("Popularity"),self.Popularity)
        # self.Length=int(data.get("Length"),self.Length)
        
        meta=data.get("Meta")
        if isinstance(meta,dict):
            for k in ["Name","Description"]:
                if k in meta.keys():
                    self.adapt_variable(k,meta[k])
            # self.Name=meta.get("Name","")
            # self.Description=meta.get("Description","")
            
            publ=meta.get("Publisher")
            if isinstance(publ,dict):
                self.Publisher=publ.get("name","")
            
        return self
    def __repr__(self) -> str:
        return f"GDDLLevel[{self.Name} by {self.Publisher} {self.ID}]"
    
if __name__ == "__main__":
    import json,requests
    data=json.loads(requests.get("https://gdladder.com/api/levels/73214186",headers = {
        "User-Agent": "",
        "accept": "application/json"
    }).content)
    print(GDDLLevel().load(data))