from enum import Enum
from typing import Literal
from nonebot import get_driver,require
from .plat_sheets import LevelEntry,TheListsEntry,PlatChartEntry
from .gd_data import PLAT_CHART_CACHE,PLAT_SHEET_CACHE,PEMONLIST_CACHE,AREDL_CACHE,UNDERRATED_CACHE,AREDLLevel,PemonlistLevel
from .underrated_data import UnderratedLevel,formatUnderrated
from . import formatters

require('bbot_api')
from ..bbot_api.message_compat import TextImageMessage
require('gd_api')
from ..gd_api.gd import Difficulty,Length
from ..gd_api import gd
from ..gd_api.gd import Level as GDLevel
from ..gd_api.thumbs import getThumbnail_async,getThumbnailUrl
from ..gd_api.gddl import GDDLLevel
require('bbot_render')
from ..bbot_render.models import LevelLargeRenderArgs

class GDLevelInfoProvider:
    level_id:int=0
    
    dc_entry:PlatChartEntry|None=None
    dc_entries:list[PlatChartEntry]
    
    dc_challenges:list[PlatChartEntry]
    
    nlwlike_entry:TheListsEntry|None=None
    nlwlike_entries:list[TheListsEntry]
    underrated_entry:UnderratedLevel|None=None
    underrated_entries:list[UnderratedLevel]
    aredl_entry:AREDLLevel|None=None
    aredl_entries:list[AREDLLevel]
    pemonlist_entry:PemonlistLevel|None=None
    pemonlist_entries:list[PemonlistLevel]
    
    def __init__(self,level_id:int) -> None:
        self.level_id=level_id
        self.dc_entries=[]
        self.dc_challenges=[]
        self.nlwlike_entries=[]
        self.underrated_entries=[]
        self.aredl_entries=[]
        self.pemonlist_entries=[]
        
    # is_demon and is_plat are for optimizing the fetching, skipping unnecessary lookups in irrevelant caches. None values forces lookups in all caches.
    # is_demon and is_plat are for optimizing the fetching, skipping unnecessary lookups in irrevelant caches. None values forces lookups in all caches.
    def fetch(self,is_demon:bool|None=None,is_plat:bool|None=None):
        id=self.level_id
        dc_entry=None
        dc_entries:list[PlatChartEntry]=[]
        # Check Difficulty Chart for platformers
        # if level.is_plat():
        dc_entries=[e for e in PLAT_CHART_CACHE.get_for_id(id) if not e.challenge]
        if dc_entries:
            dc_entry=dc_entries[0]
            dc_challenges=PLAT_CHART_CACHE.get_challenges_for_level(dc_entry)
                
        nlwlike_entry=None
        nlwlike_entries:list[TheListsEntry]=[]
        # Check NLW-like for pemons
        if is_demon or (is_demon is None):
            nlwlike_entries=PLAT_SHEET_CACHE.get_for_id(id)
            nlwlike_entries.sort(key=lambda x: 1 if x.is_legacy() else 0)
            
            if nlwlike_entries:
                nlwlike_entry=nlwlike_entries[0]
        
        underrated_entry=None
        underrated_entries:list[UnderratedLevel]=[]
        # Check underrated levels for non-demons
        if not is_demon or (is_demon is None):
            underrated_entries=UNDERRATED_CACHE.get_for_id(id)
            if underrated_entries:
                underrated_entry=underrated_entries[0]
                
        aredl_entry=None
        aredl_entries:list[AREDLLevel]=[]
        if is_demon or (is_demon is None):
            aredl_entries=AREDL_CACHE.get_for_id(id)
            aredl_entry=aredl_entries[0] if aredl_entries else None
            
        pemonlist_entry=None
        pemonlist_entries:list[PemonlistLevel]=[]
        if (is_demon or (is_demon is None)) and (is_plat or (is_plat is None)):
            pemonlist_entries=PEMONLIST_CACHE.get_for_id(id)
            pemonlist_entry=pemonlist_entries[0] if pemonlist_entries else None
            
        self.dc_entry=dc_entry
        self.dc_entries=dc_entries
        self.dc_challenges=dc_challenges
        
        self.nlwlike_entry=nlwlike_entry
        self.nlwlike_entries=nlwlike_entries
        self.underrated_entry=underrated_entry
        self.underrated_entries=underrated_entries
        self.aredl_entry=aredl_entry
        self.aredl_entries=aredl_entries
        self.pemonlist_entry=pemonlist_entry
        self.pemonlist_entries=pemonlist_entries
        
    def fillRenderArgs(self,imargs:LevelLargeRenderArgs):
        dc_entry=self.dc_entry
        dc_entries=self.dc_entries
        pemonlist_entry=self.pemonlist_entry
        pemonlist_entries=self.pemonlist_entries
        aredl_entry=self.aredl_entry
        aredl_entries=self.aredl_entries
        underrated_entry=self.underrated_entry
        underrated_entries=self.underrated_entries
        nlwlike_entry=self.nlwlike_entry
        nlwlike_entries=self.nlwlike_entries
        
        if dc_entry:
            imargs.weight = str(dc_entry.weight or '-')
            imargs.pemonlist = str(dc_entry.pemon or '-')
            imargs.diffchart_tier = dc_entry.tier or ''
            imargs.diffchart_tags = ','.join(dc_entry.tags)
            
        if pemonlist_entry:
            imargs.pemonlist = str(pemonlist_entry.placement or '-')
            
        if aredl_entry:
            imargs.aredl_pos = str(aredl_entry.position or '-')
            imargs.aredl_tags =  ", ".join(aredl_entry.tags)
            
        if underrated_entry:
            imargs.underrated_tier = f"{underrated_entry.tier} ({underrated_entry.get_tier_reference()})"
            imargs.underrated_tags =  ", ".join(underrated_entry.skillsets)
            
        if nlwlike_entry:
            imargs.nlw_type =  nlwlike_entry.sheet
            imargs.nlw_tier =  nlwlike_entry.get_section()
            imargs.nlw_tags =  ", ".join(nlwlike_entry.skillsets)
            
        if nlwlike_entries:
            for l in nlwlike_entries:
                if l.checkpoints: 
                    imargs.checkpoints=l.checkpoints.replace("∞","Infinite")
                    break
                
        description2_lines:list[str]=[]
        if aredl_entry and aredl_entry.description:
            description2_lines.append("AREDL Description:\n"+aredl_entry.description)
        if nlwlike_entry and nlwlike_entry.description:
            description2_lines.append(nlwlike_entry.sheet+" Description:\n"+nlwlike_entry.description)
        if underrated_entry and underrated_entry.desc:
            description2_lines.append("Underrated Levels Description:\n"+underrated_entry.desc)
            
        description2="\n".join(description2_lines)
        imargs.description2=description2
        
    def getTextDescription(self,image_shown:bool):
        dc_entry=self.dc_entry
        dc_entries=self.dc_entries
        pemonlist_entry=self.pemonlist_entry
        pemonlist_entries=self.pemonlist_entries
        aredl_entry=self.aredl_entry
        aredl_entries=self.aredl_entries
        underrated_entry=self.underrated_entry
        underrated_entries=self.underrated_entries
        nlwlike_entry=self.nlwlike_entry
        nlwlike_entries=self.nlwlike_entries
        lines:list[str]=[]
        if dc_entries:
            lines.append("--Difficulty Chart--")
            for e in dc_entries:
                lines.append(formatters.formatDiffChart(e,False,True))
                
            for e in self.dc_challenges:
                lines.append(f"--{e.challenge}--")
                lines.append(formatters.formatDiffChart(e,False,True))
                # lines.append(f"({e.challenge}): T{e.tier} W{e.weight or '-'}")
            
        if (not dc_entries) and pemonlist_entry:
            lines.append(formatters.formatPemonlist(pemonlist_entry,False,True)) 
            
        if aredl_entries:
            lines.append("--AREDL--")
            for e in aredl_entries:
                lines.append(formatters.formatAREDLLevel(e,False,True,not image_shown))
                
        if underrated_entries:
            lines.append("--Underrated Levels--")
            for e in underrated_entries:
                lines.append(formatUnderrated(e,False,True,not image_shown))
        
        if nlwlike_entries:
            lines.append("--NLW/IDS/HDS--")
            for e in nlwlike_entries:
                lines.append(formatters.formatListsLevel(e,False,True,not image_shown))
        return lines