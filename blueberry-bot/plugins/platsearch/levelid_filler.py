import os
import time
from typing import Callable, Sequence, TypeVar
from cachetools import TTLCache, cached
from nonebot import logger, require
import yaml

from .plat_sheets import TheListsEntry,PlatChartEntry
from . import plat_sheets

require('gd_api')
from ..gd_api import gddl
from ..gd_api.gddl import GDDLLevel

ENTRY_TYPE = TypeVar(name="ENTRY_TYPE",bound=TheListsEntry|PlatChartEntry)

NameMappingEntry=tuple[str,int]

class FillerMapping:
    author_names:dict[str,str]
    fixed_levels:dict[str,int]
    
    # Name: (Publisher, ID)
    names_to_levels:dict[str,list[NameMappingEntry]]={}
    
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
        
        logger.info(f"Loaded {self.author_names.__len__()} author name overrides.")
        logger.debug(self.author_names)
        
        logger.info(f"Loaded {self.fixed_levels.__len__()} level overrides.")
        logger.debug(self.fixed_levels)
        
        return self
        
    def map_creator(self,name:str):
        return self.author_names.get(name,name)
    
    def map_level(self,levelname:str,levelauthor:str):
        return self.fixed_levels.get(levelname+"@"+levelauthor)
    
    def fillIDForEntry(self,level:TheListsEntry|PlatChartEntry):
        
        id=self.map_level(level.name,str(level.creator))
        if id:
            return id
        
        entries=self.getEntriesForName(level.name)
        
        for creator,id in entries:
            if level.creator and self.map_creator(creator).lower().strip() in level.creator.lower():
                level.id=id
                return id
    
    def getEntriesForName(self,name:str):
        key=name.lower().strip()
        if key not in self.names_to_levels:
            self.names_to_levels[key]=[]
        return self.names_to_levels[key]
    
    @cached(TTLCache(maxsize=1,ttl=10))
    def loadNamesToLevelMappings(self):
        self.names_to_levels.clear()
        levels=gddl.getGDDLUntiered()
        if not levels:
            return
        for id,level in levels.items():
            entries=self.getEntriesForName(level.Name)
            if (level.Publisher,level.ID) in entries:
                continue
            entries.append((level.Publisher,level.ID))
                    
FILLER_MAPPING=FillerMapping()
FILLER_MAPPING.load()
            
def fillIDsForEntries(entries:Sequence[ENTRY_TYPE]):
    
    FILLER_MAPPING.load()
    # if NAMES_TO_LEVEL.__len__()==0:
    FILLER_MAPPING.loadNamesToLevelMappings()
    levels_not_matched:list[ENTRY_TYPE]=[]
    for i in entries:
        id=FILLER_MAPPING.fillIDForEntry(i)
        if not id:
            levels_not_matched.append(i)
            
    return levels_not_matched

# Name: (Publisher, ID)
NAMES_TO_LEVEL:dict[str,list[tuple[str,int]]]={}


def get_plat_chart():
    results=plat_sheets.get_plat_chart()
    fillIDsForEntries(results)
    return results

def get_3_lists():
    results=plat_sheets.get_3_lists()
    fillIDsForEntries(results)
    return results