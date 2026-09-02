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
    Deviation:float|None=None
    RatingCount:int=0
    EnjoymentCount:int=0
    SubmissionCount:int=0
    TwoPlayerRating:float|None=None
    TwoPlayerEnjoyment:float|None=None
    TwoPlayerDeviation:float|None=None
    DefaultRating:float|None=None
    Showcase:str=""
    Popularity:float|None=None
    # Meta ID
    MetaID:int=0
    # From Meta
    Name:str=""
    Description:str=""
    Length:int=0
    IsTwoPlayer:bool=False
    Difficulty:GDDLDifficulty=GDDLDifficulty.OFFICIAL
    SongID:int=0
    PublisherID:int=0
    UploadedAt:str|None=None
    # From Meta/Publisher/name
    Publisher:str=""
    # From Meta/Song
    SongName:str=""
    SongAuthor:str=""
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
        for k in ["ID","Rating","Enjoyment","Deviation","RatingCount",
                   "EnjoymentCount","SubmissionCount","TwoPlayerRating",
                   "TwoPlayerEnjoyment","TwoPlayerDeviation","DefaultRating",
                   "Showcase","Popularity"]:
            if k in data.keys():
                self.adapt_variable(k,data[k])
        
        meta=data.get("Meta")
        if isinstance(meta,dict):
            if "ID" in meta:
                self.adapt_variable("MetaID",meta["ID"])
            for k in ["Name","Description","Length","IsTwoPlayer","Difficulty","SongID","PublisherID","UploadedAt"]:
                if k in meta.keys():
                    self.adapt_variable(k,meta[k])
            
            publ=meta.get("Publisher")
            if isinstance(publ,dict):
                self.Publisher=publ.get("name","")
            elif isinstance(publ,str):
                self.Publisher=publ
            
            song=meta.get("Song")
            if isinstance(song,dict):
                self.SongName=song.get("Name","")
                self.SongAuthor=song.get("Author","")
            
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