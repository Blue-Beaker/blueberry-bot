
from typing import override
from nonebot import get_driver,require,logger

require('bbot_api')
from ..bbot_api.sheets_api import Sheet,list_sheet_names
from ..bbot_api import safeConversion

from .models import BaseSerializableEntry
from .utils import split_str_lists

PLAT_RANK_ID="1uicngbhpej4PEmtYYeGmYlFsA28PwTzzouWb4EWQkTY"

class PlatRankPlayer(BaseSerializableEntry):
    date:str=""
    name:str=""
    pronouns:str=""
    input_device:str=""
    region:str=""
    ranking:int=99999999
    points:float=99999999
    hardest_levels:list[str]=[]
    verifications:list[str]=[]
    first_victors:list[str]=[]
    def __init__(self) -> None:
        self.hardest_levels=[]
        self.verifications=[]
        self.first_victors=[]
    
    def parseLine(self,line:list[str]):
        line=[line[i] if len(line)>i else "" for i in range(0,20)]
        
        self.date=line[0]
        self.name=line[2]
        self.pronouns=line[3]
        self.input_device=line[4]
        self.region=line[5]
        self.ranking=safeConversion(line[6],int,99999999)
        self.points=safeConversion(line[7],float,99999999.0)
        self.hardest_levels=[]
        for i in range(8,18):
            self.hardest_levels.append(str(line[i]))
        self.verifications=split_str_lists(line[18])
        self.first_victors=split_str_lists(line[19])
        return self
    
    def __repr__(self) -> str:
        return f"PlatRankPlayer #{self.ranking}: {self.name}, points:{self.points}"
    
    def exactMatch(self,search:str):
        return search.lower().strip() == self.name.lower().strip()
    def matchesName(self,search:str,fuzzy_match:bool=False):
        if fuzzy_match:
            return search.lower() in self.name.lower()
        else:
            return self.exactMatch(search)
        
class PlatRankSheet(Sheet):
    def __init__(self, id: str) -> None:
        super().__init__(id, "")
        self.ready=False
    def set_range(self,range:str):
        self.range=range
    def refresh_range(self):
        sheet_names:list[str]=list_sheet_names(PLAT_RANK_ID)
        logger.info(f"Platformer Rank Sheet Names: {sheet_names}")
        
        tab_name=None
        for name in sheet_names:
            if "season" in name.lower():
                tab_name=name
                break
            
        if not tab_name:
            self.ready=False
            logger.info(f"Didn't find Platformer Rank data")
            return
        self.set_range(f"{tab_name}!A2:T")
        self.ready=True
        logger.info(f"Found Platformer Rank data in {tab_name}")
        
    def is_ready(self):
        return self.ready
    @override
    def get(self):
        return super().get() if self.ready else None
    
def parse_plat_rank(lines:list[list[str]]):
    results:list[PlatRankPlayer]=[]
    for line in lines:
        player=PlatRankPlayer().parseLine(line)
        if not player.name or player.name=="secret invisible header":
            continue
        if player.name=="Most recent completion":
            break
        results.append(player)
        
    return results

def get_plat_rank() -> list[PlatRankPlayer]:
    PLAT_RANK_SHEET.refresh_range()
    lines=PLAT_RANK_SHEET.get()
    if lines:
        return parse_plat_rank(lines)
    else:
        return []
    
PLAT_RANK_SHEET=PlatRankSheet(PLAT_RANK_ID)