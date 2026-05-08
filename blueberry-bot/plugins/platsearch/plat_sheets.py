
import re
from cachetools import cached, TTLCache

from .sheets_api import Sheet

PLAT_RANK_ID = "1uicngbhpej4PEmtYYeGmYlFsA28PwTzzouWb4EWQkTY"

    
PLAT_RANK_WEIGHTS = Sheet(PLAT_RANK_ID,"Weight!A2:E")

HDS_PLAT = Sheet("1M7C58CG_5cLGsJEXTLQBtO6nzbpA-1zxCb8ZV8ux3zg","THE Plat List!A2:H")
IDS_PLAT = Sheet("15ehtAIpCR8s04qIb8zij9sTpUdGJbmAE_LDcfVA3tcU","Tha Platformer Levels!A2:G")
NLW_PLAT = Sheet("1YxUE2kkvhT2E6AjnkvTf-o8iu_shSLbuFkEFcZOvieA","Tha Plevles!B2:H")

UPI_SHEET = Sheet("13rpmCGCC8NKvRJhVcUuxixUdEuc_I6rm9LlwgB2HAsM","Levels!A2:E")
DIFFICULTY_CHART = Sheet("1ApwiAVAcBmfyoPW3wvDzc8JvY4Lfg5tFsPlYg3DNWhc","The Chart!A4:G")

class LevelEntry:
    name:str
    def matchesName(self,search:str,fuzzy_match:bool=False):
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

class PlatRankEntry(LevelEntry):
    def __init__(self,section:str,name:str,weight:str|None=None) -> None:
        self.section=section
        self.name=name
        self.weight=weight
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} : {self.weight} ({self.section})"

@cached(cache=TTLCache(maxsize=20,ttl=30))
def plat_rank_weights():
    results:list[PlatRankEntry]=[]
    values=PLAT_RANK_WEIGHTS.get()
    if values:
        current_section=""
        for line in values:
            level=line[0]
            weight=line[1]
            if not weight:
                current_section=level.removesuffix("Placements").strip()
                continue
            
            misc_place=[i.strip() for i in line[2].split(",")]
            pemonlist_place=[i.strip() for i in line[3].split(",")]
            
            results.append(PlatRankEntry(current_section,level,weight))
            
    return results

class TheListsEntry(LevelEntry):
    def __init__(self,sheet:str,section:str,name:str,creator:str|None=None,checkpoints:str|None=None,skillsets:list[str]=[],description:str|None=None) -> None:
        self.sheet=sheet
        self.section=section
        self.name=name
        self.creator=creator
        self.checkpoints=checkpoints
        self.skillsets=skillsets
        self.description=description
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} by {self.creator} in {self.section}"
        
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
            results.append(TheListsEntry("HDS",current_section,level,creator,checkpoints,skillsets,desc))
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
            results.append(TheListsEntry("IDS",current_section,level,creator,checkpoints,skillsets,desc))
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
                current_section=level.removeprefix("|").strip()
                continue
            creator=line[1]
            if not level:
                current_section="WTH IS THIS"
            checkpoints=line[2]
            skillsets=[i.strip() for i in line[3].split(",")]
            desc=line[5]
            results.append(TheListsEntry("NLW",current_section,level,creator,checkpoints,skillsets,desc))
    return results

def get_3_lists():
    results:list[TheListsEntry]=[]
    results.extend(get_hds())
    results.extend(get_ids())
    results.extend(get_nlw())
    return results

class PlatChartEntry(LevelEntry):
    def __init__(self,id:int,name:str,tier:str="",creator:str="",tags:list[str]=[],enj:str="") -> None:
        self.name=name
        self.id=id
        self.tier=tier
        self.creator=creator
        self.tags=tags
        self.enj=enj
        self.tpl:str|None=None
        self.weight:str|None=None
        self.pemon:str|None=None
    def __repr__(self) -> str:
        return "Level:"+", ".join([f"{k}:{v}"for k,v in self.__dict__.items()])
    def __str__(self):
        return f"{self.name} {self.id}"
    
    @classmethod
    def build(cls,tier:str,line:list[str]):
        name=line[0]
        id=safeInt(line[2])
        creator=line[3]
        tags=[i.strip() for i in line[4].split(",") if i != "---"]
        enj=line[5]
        return PlatChartEntry(id,name,tier,creator,tags,enj)
    
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
                id = int(line[0])
                tpl=line[3]
                pemon=line[4]
                entry=id_to_levels.get(id)
                if not entry:
                    entry=PlatChartEntry(id,line[1],line[2])
                    results.append(entry)
                entry.tpl=tpl if tpl!="-" else None
                entry.pemon=pemon if pemon!="-" else None
            except:
                pass
            
    weights=plat_rank_weights()
    for level in weights:
        entry = name_to_levels.get(level.nameKey(),None)
        if not entry:
            entry=PlatChartEntry(-1,level.name,"")
        entry.weight=level.weight

    return results

def safeInt(i:str):
    try:
        return int(i)
    except:
        return -1