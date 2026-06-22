import os
from typing import TypeVar
from nonebot import logger, require
import yaml

from .plat_sheets import TheListsEntry,PlatChartEntry

require('gd_api')
from ..gd_api import gddl
from ..gd_api.gddl import GDDLLevel

ENTRY_TYPE = TypeVar(name="ENTRY_TYPE",bound=TheListsEntry|PlatChartEntry)

class FillerMapping:
    author_names:dict[str,str]
    fixed_levels:dict[str,int]
    def __init__(self) -> None:
        self.author_names={}
        self.fixed_levels={}
    def load(self,path:str="config/filler_mapping.yaml"):
        if not os.path.exists(path):
            logger.info(f"Config {path} not found. Not loading mappings")
            return
        with open(path,"r") as f:
            data=yaml.load(f,yaml.BaseLoader)
            
        if not isinstance(data,dict):
            return
        self.author_names=data.get("author_names",{})
        self.fixed_levels=data.get("fixed_levels",{})
        
        logger.info(self.author_names)
        logger.info(self.fixed_levels)
        
        return self
        
    def map_creator(self,name:str):
        return self.author_names.get(name,name)
    
    def map_level(self,levelname:str,levelauthor:str):
        return self.fixed_levels.get(levelname+"@"+levelauthor)
    
    def fillIDForEntry(self,level:TheListsEntry|PlatChartEntry):
        
        id=self.map_level(level.name,str(level.creator))
        if id:
            return id
        
        if level.name in NAMES_TO_LEVEL:
            entries=NAMES_TO_LEVEL[level.name]
            
            for creator,id in entries:
                if level.creator and self.map_creator(creator).lower().strip() in level.creator.lower():
                    level.id=id
                    return id
                    
FILLER_MAPPING=FillerMapping()
FILLER_MAPPING.load()
            
def fillIDsForEntries(results:list[ENTRY_TYPE]):
    if NAMES_TO_LEVEL.__len__()==0:
        loadNamesToLevelMappings()
    levels_not_matched:list[ENTRY_TYPE]=[]
    for i in results:
        id=FILLER_MAPPING.fillIDForEntry(i)
        if not id:
            levels_not_matched.append(i)
            
    return levels_not_matched

# Name: (Publisher, ID)
NAMES_TO_LEVEL:dict[str,list[tuple[str,int]]]={}

def loadNamesToLevelMappings():
    NAMES_TO_LEVEL.clear()
    levels=gddl.getGDDLUntiered()
    if not levels:
        return
    for id,level in levels.items():
        name=level.Name
        if name not in NAMES_TO_LEVEL:
            NAMES_TO_LEVEL[name]=[]
        if (level.Publisher,level.ID) in NAMES_TO_LEVEL[name]:
            continue
        NAMES_TO_LEVEL[name].append((level.Publisher,level.ID))
