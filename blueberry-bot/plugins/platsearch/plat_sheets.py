
import re
from typing import Any, TypeVar
from cachetools import cached, TTLCache
from nonebot import require

require('bbot_api')
from ..bbot_api.sheets_api import Sheet
require('gd_api')
from ..gd_api import gddl
from ..gd_api.gddl import GDDLLevel 

PLAT_RANK_ID = "1uicngbhpej4PEmtYYeGmYlFsA28PwTzzouWb4EWQkTY"

    
PLAT_RANK_WEIGHTS = Sheet(PLAT_RANK_ID,"Weight!A2:E")

HDS_PLAT = Sheet("1M7C58CG_5cLGsJEXTLQBtO6nzbpA-1zxCb8ZV8ux3zg","THE Plat List!A2:H")
IDS_PLAT = Sheet("15ehtAIpCR8s04qIb8zij9sTpUdGJbmAE_LDcfVA3tcU","Tha Platformer Levels!A2:G")
NLW_PLAT = Sheet("1YxUE2kkvhT2E6AjnkvTf-o8iu_shSLbuFkEFcZOvieA","Tha Plevles!B2:H")

UPI_SHEET = Sheet("13rpmCGCC8NKvRJhVcUuxixUdEuc_I6rm9LlwgB2HAsM","Levels!A2:E")
DIFFICULTY_CHART = Sheet("1ApwiAVAcBmfyoPW3wvDzc8JvY4Lfg5tFsPlYg3DNWhc","The Chart!A4:G")

class BaseLevelEntry:
    id:int=0
    def to_dict(self) -> dict:
        return self.__dict__
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.__dict__.update(data)
        return inst
    
class LevelEntry(BaseLevelEntry):
    name:str
    def exactMatch(self,search:str):
        return search.lower().replace("(","").replace(")","").strip() == self.name.lower().replace("(","").replace(")","").strip()
    def matchesName(self,search:str,fuzzy_match:bool=False):
        if self.exactMatch(search):
            return True
        if fuzzy_match:
            return search.lower() in self.name.lower()
        else:
            patt = re.compile(r"(.*)\(.*\)")
            matched=patt.match(self.name)
            name=self.name
            if matched:
                name=matched.group(1)
            return search.lower().strip() == name.lower().strip()
    def nameKey(self):
        return self.name.lower().strip()

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
            level=line[0]
            weight=safeInt(line[1],None)
            
            if not weight:
                current_section=level.removesuffix("Placements").strip()
                continue
            
            misc_place=[i.strip() for i in line[2].split(",")]
            pemonlist_place=[i.strip() for i in line[3].split(",")]
            
            results.append(PlatWeight().update(current_section,level,weight))
            
    return results

class TheListsEntry(LevelEntry):
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
    results:list[TheListsEntry]=[]
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
            skillsets=[i.strip() for i in line[5].split(",")]
            desc=line[6]
            results.append(TheListsEntry().update("HDS",current_section,level,creator,checkpoints,skillsets,desc))
    return results
            
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_ids():
    results:list[TheListsEntry]=[]
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
            skillsets=[i.strip() for i in line[4].split(",")]
            desc=line[5]
            results.append(TheListsEntry().update("IDS",current_section,level,creator,checkpoints,skillsets,desc))
    return results
            
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_nlw():
    results:list[TheListsEntry]=[]
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
                # current_section="WTH IS THIS"
                break
            
            if level=="None Yet!" and not creator:
                break
            
            checkpoints=line[2]
            skillsets=[i.strip() for i in line[3].split(",")]
            desc=line[5]
            results.append(TheListsEntry().update("NLW",current_section,level,creator,checkpoints,skillsets,desc))
    return results

def get_3_lists():
    results:list[TheListsEntry]=[]
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
        return self
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} {self.id}"
    
    def has_skills(self,search:list[str]):
        return has_skills(search,self.tags)
    
    @classmethod
    def build(cls,tier:str,line:list[str]):
        name=line[0]
        id=safeInt(line[2])
        creator=line[3]
        tags=[i.strip() for i in line[4].split(",") if i != "---"]
        enj=line[5]
        return PlatChartEntry().update(id,name,tier,creator,tags,enj)
    
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
    
    upi=UPI_SHEET.get()
    if upi:
        for line in upi:
            try:
                id = safeInt(line[0])
                name=line[1]
                # Skip challenges like Evernight (Coin), Storm Front (Deathless) etc.
                if "(" in name or ")" in name:
                    continue
                
                tier=line[2]
                tier=tier if tier!="P" else None
                tpl=line[3]
                tpl=tpl if tpl!="-" else None
                pemon=line[4]
                pemon=pemon if pemon!="-" else None
                entry=id_to_levels.get(id)
                
                if not entry and (tier or tpl or pemon):
                    entry=PlatChartEntry().update(id,name,tier)
                    results.append(entry)
                    
                if entry:
                    entry.tpl=safeInt(tpl,None)
                    entry.pemon=safeInt(pemon,None)
                
            except:
                pass
            
    weights=plat_rank_weights()
    for level in weights:
        entry = name_to_levels.get(level.nameKey(),None)
        if not entry:
            entry=PlatChartEntry().update(-1,level.name,"")
        entry.weight=level.weight
        entry.weight_type=level.section

    return results

def has_skills(search:list[str],level_skills:list[str],skill_groups:list[list[str]]=[]):
    lskills=set()
    for s in level_skills:
        lskills.add(s.lower())
        if " " in s:
            lskills.add(s.lower().replace(" ",""))
    
    for group in skill_groups:
        intersect=list(set(group) & set(lskills))
        if intersect:
            lskills=list(set(group) | set(lskills))
    matched=True
    for s in search:
        if s.lower() not in lskills:
            matched=False
            break
    return matched

_A = TypeVar(name="_A")
def safeInt(i:Any,fallback:_A=-1) -> int|_A:
    try:
        return int(i)
    except:
        return fallback
