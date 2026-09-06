
import re
from typing import Any, TypeVar, override
from cachetools import cached, TTLCache
from nonebot import require

require('bbot_api')
from ..bbot_api.sheets_api import SheetRange
require('gd_api')
from ..gd_api import gddl
from ..gd_api.gddl import GDDLLevel 

from .data_cache import CacheWithIDMap,KeyMapCache
from .models import LevelEntry
from .utils import split_str_lists,has_skills,safeInt

PLAT_RANK_ID = "1uicngbhpej4PEmtYYeGmYlFsA28PwTzzouWb4EWQkTY"

    
PLAT_RANK_WEIGHTS = SheetRange(PLAT_RANK_ID,"Weight!A2:E")

HDS_PLAT = SheetRange("1M7C58CG_5cLGsJEXTLQBtO6nzbpA-1zxCb8ZV8ux3zg","THE Plat List!A2:H")
IDS_PLAT = SheetRange("15ehtAIpCR8s04qIb8zij9sTpUdGJbmAE_LDcfVA3tcU","Tha Platformer Levels!A2:G")
NLW_PLAT = SheetRange("1YxUE2kkvhT2E6AjnkvTf-o8iu_shSLbuFkEFcZOvieA","Tha Plevles!B2:H")

UPI_SHEET = SheetRange("13rpmCGCC8NKvRJhVcUuxixUdEuc_I6rm9LlwgB2HAsM","Levels!A2:E")
DIFFICULTY_CHART = SheetRange("1ApwiAVAcBmfyoPW3wvDzc8JvY4Lfg5tFsPlYg3DNWhc","The Chart!A4:G")

PATTERN_CHALLENGE = re.compile(r"(.*)\((.*?)\)")
CHALLENGE_TYPES = set(['deathless','coin','unnerfed','nerfed'])

BASENAME_REGEX = re.compile(r"(.*)\((.*)\)")

class PlatWeight(LevelEntry):
    def update(self,section:str,name:str,weight:int|None=None):
        self.section=section
        self.name=name
        self.weight=weight
        return self
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} : {self.weight} ({self.section})"

@cached(cache=TTLCache(maxsize=20,ttl=30))
def plat_rank_weights():
    results:list[PlatWeight]=[]
    values=PLAT_RANK_WEIGHTS.get()
    if values:
        current_section=""
        for line in values:
            while len(line)<4:
                line.append("")
            level=line[0]
            weight=safeInt(line[1],None)
            
            if not weight:
                if level.strip().lower()=="secret header":
                    continue
                current_section=level.removesuffix("Placements").strip()
                continue
            
            misc_place=split_str_lists(line[2])
            pemonlist_place=split_str_lists(line[3])
            
            results.append(PlatWeight().update(current_section,level,weight))
            
    return results

class NLWLikeEntry(LevelEntry):
    id:int=0
    def update(self,sheet:str,section:str,name:str,creator:str|None=None,checkpoints:str|None=None,skillsets:list[str]=[],description:str|None=None):
        self.sheet=sheet
        self.section=section
        self.name=name
        self.creator=creator
        self.checkpoints=checkpoints
        self.skillsets=skillsets
        self.description=description
        return self
    def has_skills(self,search:list[str]):
        return has_skills(search,self.skillsets,[["dash orbs","wavedash"]])
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} by {self.creator} in {self.section}"
    def is_legacy(self):
        sect=self.section.lower()
        return ("rerates" in sect) or ("legacy" in sect)
    def is_pending(self):
        sect=self.section.lower()
        return sect in ["plending","pending"]
    def is_main(self):
        return not (self.is_legacy() or self.is_pending())
    def get_section(self):
        return self.section.replace("Fuck","Fxxk")
        
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_hds():
    results:list[NLWLikeEntry]=[]
    values=HDS_PLAT.get()
    if values:
        current_section=""
        for line in values:
            while line.__len__()<7:
                line.append("")
            level=line[0]
            if level.startswith("↓"):
                current_section=level.removeprefix("↓").removesuffix("↓").strip()
                continue
            creator=line[2]
            checkpoints=line[3]
            skillsets=split_str_lists(line[5])
            desc=line[6]
            results.append(NLWLikeEntry().update("HDS",current_section,level,creator,checkpoints,skillsets,desc))
    return results
            
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_ids():
    results:list[NLWLikeEntry]=[]
    values=IDS_PLAT.get()
    if values:
        current_section=""
        for line in values:
            while line.__len__()<7:
                line.append("")
            level=line[0]
            if level.startswith("↓"):
                current_section=level.removeprefix("↓").removesuffix("↓").strip()
                continue
            creator=line[2]
            checkpoints=line[3]
            skillsets=split_str_lists(line[4])
            desc=line[5]
            results.append(NLWLikeEntry().update("IDS",current_section,level,creator,checkpoints,skillsets,desc))
    return results
            
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_nlw():
    results:list[NLWLikeEntry]=[]
    values=NLW_PLAT.get()
    if values:
        current_section=""
        for line in values:
            while line.__len__()<7:
                line.append("")
            level=line[0]
            if level.startswith("|"):
                current_section=level.removeprefix("|").strip().removesuffix(" Tier")
                continue
            creator=line[1]
            if not level and not creator:
                continue
                # # current_section="WTH IS THIS"
                # break
            
            if level=="None Yet!" and not creator:
                break
            
            checkpoints=line[2]
            skillsets=split_str_lists(line[3])
            desc=line[5]
            results.append(NLWLikeEntry().update("NLW",current_section,level,creator,checkpoints,skillsets,desc))
    return results

def get_nlw_like():
    results:list[NLWLikeEntry]=[]
    results.extend(get_hds())
    results.extend(get_ids())
    results.extend(get_nlw())
    return results

class PlatChartEntry(LevelEntry):
    id:int=0
    tpl:int|None
    pemon:int|None
    weight:int|None
    weight_type:str|None
    tags:list[str]=[]
    name:str=""
    tier:str|None=None
    creator:str=""
    enj:str=""
    
    basename:str|None=None
    challenge:str|None=None
    
    def __init__(self) -> None:
        super().__init__()
        self.tpl=None
        self.pemon=None
        self.weight=None
        self.weight_type=None
    def update(self,id:int,name:str,tier:str|None="",creator:str="",tags:list[str]=[],enj:str=""):
        self.name=name
        self.id=id
        self.tier=tier
        self.creator=creator
        self.tags=tags
        self.enj=enj
        self._fill_split_name_challenge()
        return self
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} {self.id}"
    
    def has_skills(self,search:list[str]):
        return has_skills(search,self.tags)
    
    def get_basename(self):
        return self.basename or self.name
    
    # Fill in challenge (No coin/deathless/unnerfed...) and basename (resting parts)
    def _fill_split_name_challenge(self):
        matched = PATTERN_CHALLENGE.match(self.name)
        if not matched:
            return None
        basename = matched.group(1).strip()
        challenge = matched.group(2).strip()
        lowspl = challenge.lower().split()
        
        for low in lowspl:
            if low in CHALLENGE_TYPES:
                self.challenge = challenge
                self.basename = basename
                break
        
        return self
        
    @classmethod
    def build(cls,tier:str,line:list[str]):
        name=line[0].strip()
        id=safeInt(line[2])
        creator=line[3].strip()
        tags=[i.strip() for i in line[4].split(",") if i != "---"]
        enj=line[5]
        return PlatChartEntry().update(id,name,tier,creator,tags,enj)
    
class PlatChartCache(CacheWithIDMap[PlatChartEntry]):
    
    def __init__(self, file_path: str | None = None, ttl: int = 3600, name: str = "UNNAMED") -> None:
        super().__init__(PlatChartEntry, file_path, ttl, name)
        def get_name(l:PlatChartEntry):
            return l.basename or l.name
        self.name_map=KeyMapCache(get_name)
        self.add_keymap(self.name_map)
        
    def get_challenges_for_level(self,l:PlatChartEntry):
        return [l for l in self.levels_for_name(l.get_basename()) if l.challenge]
    
    def levels_for_name(self,name:str):
        return self.name_map.get(name)
    
SPECIAL_LEVELID_PATTERN=re.compile('See "(.*)"')
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_plat_chart():
    
    results:list[PlatChartEntry]=[]
    id_to_levels:dict[int,PlatChartEntry]={}
    name_to_levels:dict[str,PlatChartEntry]={}
    duplicated_names:set[str]=set()
    
    values=DIFFICULTY_CHART.get()
    if values:
        tier=""
        for line in values:
            if line.__len__()==1:
                tier=line[0].removeprefix("TIER").split("-")[0].strip()
                continue
            while line.__len__()<6:
                line.append("")
                
            entry=PlatChartEntry.build(tier,line)
            # Invalid entry
            if entry.name.__contains__(".") and entry.creator=="---":
                continue
            # if entry.name or entry.id>0:
            results.append(entry)
            if entry.id>0:
                id_to_levels[entry.id]=entry
                
            key=entry.nameKey()
            
            if key not in duplicated_names:
                if key not in name_to_levels.keys():
                    name_to_levels[key]=entry
                else:
                    duplicated_names.add(key)
                    name_to_levels.pop(key,None)
                    
    from .gd_data import PEMONLIST_CACHE,TPL_CACHE
    
    for l in PEMONLIST_CACHE.getOrUpdate():
        level_id=l.getID()
        entry1=id_to_levels.get(level_id)
        if not entry1:
            entry1=PlatChartEntry().update(level_id,l.name,"?",l.creator)
            results.append(entry1)
            id_to_levels[entry.id]=entry1
        entry1.pemon=l.placement
        
    for l in TPL_CACHE.getOrUpdate():
        level_id=l.getID()
        entry1=id_to_levels.get(level_id)
        if not entry1:
            entry1=PlatChartEntry().update(level_id,l.name,"?",l.author)
            results.append(entry1)
            id_to_levels[entry.id]=entry1
        entry1.tpl=l.position
            
    weights=plat_rank_weights()
    for entry1 in weights:
        entry = name_to_levels.get(entry1.nameKey(),None)
        if not entry:
            entry=PlatChartEntry().update(-1,entry1.name,"")
        entry.weight=entry1.weight
        entry.weight_type=entry1.section

    return results
