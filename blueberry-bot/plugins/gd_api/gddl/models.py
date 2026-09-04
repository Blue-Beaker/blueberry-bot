from abc import abstractmethod
from enum import Enum
from typing import Any, ClassVar, get_type_hints
from typing_extensions import Self

from ..models import BaseAdaptingModel,LevelWithID
from ..gd.models import Difficulty as GDDifficulty,Length as GDLength


class GDDLDifficulty(Enum):
    OFFICIAL="Official"
    EASY="Easy"
    MEDIUM="Medium"
    HARD="Hard"
    INSANE="Insane"
    EXTREME="Extreme"
    
    def as_official(self):
        return _DIFFICULTY_MAP.get(self,GDDifficulty.HARD)
    
_DIFFICULTY_MAP={
    GDDLDifficulty.OFFICIAL:GDDifficulty.HARD_DEMON,
    GDDLDifficulty.EASY:GDDifficulty.EASY_DEMON,
    GDDLDifficulty.MEDIUM:GDDifficulty.MEDIUM_DEMON,
    GDDLDifficulty.HARD:GDDifficulty.HARD_DEMON,
    GDDLDifficulty.INSANE:GDDifficulty.INSANE_DEMON,
    GDDLDifficulty.EXTREME:GDDifficulty.EXTREME_DEMON
}

_OFFICIAL_LEVEL_ID_MAP={
    1:14,
    2:18,
    3:20
}
    
class GDDLTags(Enum):
    # 类型检查器需要的属性声明
    tag_name: str
    tag_desc: str
    tag_order: int
    
    CUBE=(1, "Cube", "This level has cube sections that make up a large portion of its difficulty.", 1)
    SHIP=(2, "Ship", "This level has ship sections that make up a large portion of its difficulty.", 2)
    BALL=(3, "Ball", "This level has ball sections that make up a large portion of its difficulty.", 3)
    UFO=(4, "UFO", "This level has UFO sections that make up a large portion of its difficulty.", 4)
    WAVE=(5, "Wave", "This level has wave sections that make up a large portion of its difficulty.", 5)
    ROBOT=(6, "Robot", "This level has robot sections that make up a large portion of its difficulty.", 6)
    SPIDER=(7, "Spider", "This level has spider sections that make up a large portion of its difficulty.", 7)
    SWING=(20, "Swing", "This level has swing sections that make up a large portion of its difficulty.", 8)
    NERVE_CONTROL=(8, "Nerve Control", "This level tests your consistency and ability to handle stress near the end of the level.", 9)
    MEMORY=(9, "Memory", "This level requires remembering a complex path to complete, usually with several fakes, potential routes, and/or visual obscurity.", 10)
    LEARNY=(10, "Learny", "This level needs a significant time investment in order to understand its complex/unintuitive gameplay.", 11)
    DUALS=(11, "Duals", "This level has duals that make up a large portion of its difficulty. Generally refers to asymmetrical duals.", 12)
    CHOKEPOINTS=(12, "Chokepoints", "This level contains parts with very condensed difficulty in relation to the rest of the level.", 13)
    HIGH_CPS=(13, "High CPS", "This level has several sections that require very fast (usually controlled) inputs.", 14)
    TIMINGS=(14, "Timings", "This level tests your ability to perform many very precise inputs.", 15)
    FLOW=(15, "Flow", "This level has many dynamic gameplay transitions throughout the level, forming a \"smooth\" and \"flowy\" type of gameplay.", 16)
    OVERALL=(16, "Overall", "This level has no specific skillset it tests, instead drawing on multiple skillsets in smaller proportion for its difficulty.", 17)
    GIMMICKY=(17, "Gimmicky", "This level primarily focuses on developing an experimental, unorthodox gameplay type.", 18)
    FAST_PACED=(18, "Fast-Paced", "This level has fast-moving sections (3x or 4x speed) for the majority of the level.", 19)
    SLOW_PACED=(19, "Slow-Paced", "This level has slower-moving sections (0.5x) for a large part of the level.", 20)
    
    def __new__(cls, *args):
        if len(args) == 4:
            value, tag_name, tag_desc, tag_order = args
        else:
            value, tag_name, tag_desc, tag_order = args[0]
        inst = object.__new__(cls)
        inst._value_ = value
        inst.tag_name = tag_name
        inst.tag_desc = tag_desc
        inst.tag_order = tag_order
        return inst
    
def map_official_id(id:int):
    return _OFFICIAL_LEVEL_ID_MAP.get(id,id)

class GDDLSearchLevel(LevelWithID):
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
    def get_id(self) -> int:
        return map_official_id(self.id)
    def to_gddl_level(self):
        return GDDLLevel.from_search(self)
    def __repr__(self) -> str:
        return f"GDDLSearchLevel[{self.name} by {self.publisherName} {self.id}]"
    
class GDDLLevel(LevelWithID):
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
    Rarity:int=0
    SongID:int=0
    PublisherID:int=0
    UploadedAt:str|None=None
    # From Meta/Publisher/name
    Publisher:str=""
    # From Meta/Song
    SongName:str=""
    SongAuthor:str=""
    # Tags
    tags: list['GDDLLevelTag']
    tags_eligible: bool=False
    def __init__(self) -> None:
        super().__init__()
        self.tags=[]
        
    def get_id(self) -> int:
        return map_official_id(self.ID)
    
    def get_stars(self):
        if self.Difficulty!=GDDLDifficulty.OFFICIAL:
            return 10
        else:
            return {
                1:14,
                2:14,
                3:15
            }.get(self.ID,10)
            
    def is_plat(self) -> bool:
        return self.Length-1 == GDLength.PLAT.value
    def get_length(self):
        try:
            return GDLength(self.Length-1)
        except:
            return None
        
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
            for k in ["Name","Description","Length","IsTwoPlayer","Difficulty","SongID","PublisherID","UploadedAt","Rarity"]:
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
    def load_tags(self,data:list[dict]):
        self.tags=[]
        for i in data:
            tag=GDDLLevelTag().from_dict(i)
            self.tags.append(tag)
        return self
    def __repr__(self) -> str:
        return f"GDDLLevel[{self.Name} by {self.Publisher} {self.ID}]"
    
class GDDLLevelTag(BaseAdaptingModel):
    levelID:int
    HasVoted:int
    ReactCount:int
    TagID:int
    def get_tag(self):
        return GDDLTags(self.TagID)
    
if __name__ == "__main__":
    import json,requests
    data=json.loads(requests.get("https://gdladder.com/api/levels/73214186",headers = {
        "User-Agent": "",
        "accept": "application/json"
    }).content)
    print(GDDLLevel().load(data))