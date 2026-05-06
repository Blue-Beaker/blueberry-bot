
from cachetools import cached, TTLCache

try:
    from . import sheets_api
except:
    import sheets_api

# The ID and range of a sample spreadsheet.
PLAT_RANK_ID = "1uicngbhpej4PEmtYYeGmYlFsA28PwTzzouWb4EWQkTY"

class Sheet:
    def __init__(self,id:str,range:str) -> None:
        self.id=id
        self.range=range
    def get(self):
        return sheets_api.get(self.id,self.range)
    
PLAT_RANK_WEIGHTS = Sheet(PLAT_RANK_ID,"Weight!A2:E")

HDS_PLAT = Sheet("1M7C58CG_5cLGsJEXTLQBtO6nzbpA-1zxCb8ZV8ux3zg","THE Plat List!A2:H")
IDS_PLAT = Sheet("15ehtAIpCR8s04qIb8zij9sTpUdGJbmAE_LDcfVA3tcU","Tha Platformer Levels!A2:G")
NLW_PLAT = Sheet("1YxUE2kkvhT2E6AjnkvTf-o8iu_shSLbuFkEFcZOvieA","Tha Plevles!B2:H")

def plat_rank_weight(search:str):
    results=[]
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
            
            matched=False
            
            if search in level.lower():
                matched=level
                
            if matched:
                results.append(f"{matched} ({current_section}) Weight:{weight}")
    return results


class LevelEntry:
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
    results:list[LevelEntry]=[]
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
            results.append(LevelEntry("HDS",current_section,level,creator,checkpoints,skillsets,desc))
    return results
            
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_ids():
    results:list[LevelEntry]=[]
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
            results.append(LevelEntry("IDS",current_section,level,creator,checkpoints,skillsets,desc))
    return results
            
@cached(cache=TTLCache(maxsize=20,ttl=30))
def get_nlw():
    results:list[LevelEntry]=[]
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
            results.append(LevelEntry("NLW",current_section,level,creator,checkpoints,skillsets,desc))
    return results

def get_3_lists():
    results:list[LevelEntry]=[]
    results.extend(get_hds())
    results.extend(get_ids())
    results.extend(get_nlw())
    return results