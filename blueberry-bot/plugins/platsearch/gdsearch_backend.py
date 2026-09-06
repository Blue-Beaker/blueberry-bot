from enum import Enum
from typing import Literal
from nonebot import get_driver,require
from .plat_sheets import LevelEntry,NLWLikeEntry,PlatChartEntry
from .gd_data import PLAT_CHART_CACHE,PLAT_SHEET_CACHE,PEMONLIST_CACHE,AREDL_CACHE,UNDERRATED_CACHE,AREDLLevel,PemonlistLevel,GDDL_BACKUP
from .underrated_data import UnderratedLevel,formatUnderrated,Sections as URSection
from . import formatters

require('bbot_api')
from ..bbot_api.message_compat import TextImageMessage
require('gd_api')
from ..gd_api.gd import Difficulty,Length
from ..gd_api import gd
from ..gd_api.gd import Level as GDLevel, Song as GDSong
from ..gd_api.thumbs import getThumbnail_async,getThumbnailUrl
from ..gd_api.gddl import GDDLLevel
require('bbot_render')
from ..bbot_render.models import LevelLargeRenderArgs

class GDLevelInfoProvider:
    level_id:int=0
    
    dc_entry:PlatChartEntry|None=None
    dc_entries:list[PlatChartEntry]
    
    dc_challenges:list[PlatChartEntry]
    
    nlwlike_entry:NLWLikeEntry|None=None
    nlwlike_entries:list[NLWLikeEntry]
    underrated_entry:UnderratedLevel|None=None
    underrated_entries:list[UnderratedLevel]
    aredl_entry:AREDLLevel|None=None
    aredl_entries:list[AREDLLevel]
    pemonlist_entry:PemonlistLevel|None=None
    pemonlist_entries:list[PemonlistLevel]
    
    gddl_entry:GDDLLevel|None=None
    
    gd_level:GDLevel|None=None
    gd_song:GDSong|None=None
    
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
        dc_challenges:list[PlatChartEntry]=[]
        # Check Difficulty Chart for platformers
        # if level.is_plat():
        dc_entries=[e for e in PLAT_CHART_CACHE.get_for_id(id) if not e.challenge]
        if dc_entries:
            dc_entry=dc_entries[0]
            dc_challenges=PLAT_CHART_CACHE.get_challenges_for_level(dc_entry)
                
        nlwlike_entry=None
        nlwlike_entries:list[NLWLikeEntry]=[]
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
        gddl_entry=self.gddl_entry
        
        if dc_entry:
            imargs.weight = str(dc_entry.weight or '-')
            imargs.pemonlist = str(dc_entry.pemon or '-')
            imargs.diffchart_tier = dc_entry.tier or ''
            imargs.diffchart_tags = ','.join(dc_entry.tags)
            
        if self.dc_challenges:
            dc_challenge=self.dc_challenges[0]
            imargs.challenge_name=f"{dc_challenge.challenge} ({dc_challenge.weight})"
            imargs.challenge_tier=dc_challenge.tier or ''
            imargs.challenge_tags= ','.join([t for t in dc_challenge.tags if not dc_entry or (t not in dc_entry.tags)])
            
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
                
        if gddl_entry:
            if gddl_entry.seconds and not hasattr(imargs,'length2'): imargs.length2=format_time(gddl_entry.seconds)+"\n(GDDL)"
                
        description2_lines:list[str]=[]
        if aredl_entry and aredl_entry.description:
            description2_lines.append("AREDL Description:\n"+aredl_entry.description)
        if nlwlike_entry and nlwlike_entry.description:
            description2_lines.append(nlwlike_entry.sheet+" Description:\n"+nlwlike_entry.description)
        if underrated_entry and underrated_entry.desc:
            description2_lines.append("Underrated Levels Description:\n"+underrated_entry.desc)
            
        description2="\n".join(description2_lines)
        imargs.description2=description2
        
        self._fill_gd_args(imargs)
        
        if not self.gd_level and not self.gd_song:
            self._fill_base_info(imargs)
        
    def _fill_gd_args(self,imargs:LevelLargeRenderArgs):
        if self.gd_level:
            level=self.gd_level
            
            imargs.level_id=level.id
            
            imargs.level_name=level.name
            imargs.song_id=level.songID
            imargs.creator=level.creator
            imargs.stars=level.stars
            imargs.length=level.get_length().get_name()
            imargs.difficulty=level.get_difficulty().value
            imargs.feature_level=level.epic+1 if level.featured>0 else 0
            imargs.is_plat=level.is_plat()
            imargs.coins=level.coins
            imargs.bronze_coins=not level.verifiedCoins
            imargs.downloads=level.downloads
            imargs.likes=level.likes
            imargs.description=level.get_description()
            
            if level.verification_time:
                imargs.length2=format_time(level.verification_time/240)
                
            if level.song_ids or level.sfx_ids:
                imargs.song_info=f"Songs: {len(level.song_ids or '')}, SFXs: {len(level.sfx_ids or '')}"
            
        if self.gd_song:
            song=self.gd_song
            imargs.song_author=song.artistName if song else "Unknown"
            imargs.song_name=song.name if song else "Unknown"
            
        
    def _fill_base_info(self,imargs:LevelLargeRenderArgs):
        imargs.level_id=self.level_id
        
        if self.dc_entry or self.pemonlist_entry:
            imargs.length=Length.PLAT.get_name()
            imargs.is_plat=True
        
        if self.pemonlist_entry:
            imargs.stars=10
            
        if self.gddl_entry:
            level=self.gddl_entry
            imargs.level_name=level.Name
            imargs.song_id=level.SongID
            imargs.song_author=level.SongAuthor
            imargs.song_name=level.SongName
            imargs.creator=level.Publisher
            imargs.stars=10
            if not hasattr(imargs,'length'): 
                length = level.get_length()
                imargs.length=length.get_name() if length else ''
            imargs.difficulty=level.Difficulty.as_official().value
            imargs.feature_level=level.Rarity
            if not hasattr(imargs,'is_plat'): imargs.is_plat=level.is_plat()
            imargs.description=level.Description
            
        if self.underrated_entry:
            level=self.underrated_entry
            imargs.level_name=level.name
            imargs.creator=level.creator
            imargs.difficulty=level.get_difficulty().value
            if not hasattr(imargs,'is_plat'): imargs.is_plat=level.skillsets.__contains__("Platformer")
        
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
        gddl_entry=self.gddl_entry
        lines:list[str]=[]
        
        lines.extend(self._format_gd_desc(image_shown))
        
        if gddl_entry:
            lines.append("--GDDL--")
            
            def repr_float(value:float|None):
                return f"{value:.1f}" if value is not None else '-'
            lines.append(f"Tier: {repr_float(gddl_entry.Rating)} ({gddl_entry.RatingCount}) Enjoyment: {repr_float(gddl_entry.Enjoyment)} ({gddl_entry.EnjoymentCount})")
            if gddl_entry.seconds:
                lines.append(f"Length: {format_time(gddl_entry.seconds)}")
            if gddl_entry.tags:
                lines.append(f"Tags: {', '.join([f'{t.get_tag().tag_name}/{t.ReactCount}' for t in gddl_entry.tags])}")
            if gddl_entry.Popularity:
                lines.append(f"Popularity: {repr_float(gddl_entry.Popularity)}")
            
            if gddl_entry.IsTwoPlayer:
                lines.append(f"2P Tier: {repr_float(gddl_entry.TwoPlayerRating)} Enjoyment: {repr_float(gddl_entry.TwoPlayerEnjoyment)}")
            
        
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
    
    def _format_gd_desc(self,image_shown:bool) -> list[str]:
        lines:list[str]=[]
        if not self.gd_level:
            return []
        level=self.gd_level
        lines.append(f"Version: {level.version} Game ver.: {level.game_version}")
        lines.append(f"2P: {level.two_player}, Objects: {level.objects}")
        
        if self.gd_song:
            song=self.gd_song
            lines.append(f"Song: {song.name} by {song.artistName} ({song.id})")
        
        if not image_shown:
            lines.append(f"Length: {gd.Length(level.length).name}")
            if level.verification_time:
                lines[-1]=lines[-1]+(f" ({format_time(level.verification_time/240)})")
                
            lines.append(f"Coins: {level.coins}")
            if not level.verifiedCoins:
                lines[-1]=lines[-1]+(" (Bronze)")
                
            if level.song_ids and level.sfx_ids:
                lines.append(f"Songs: {len(level.song_ids or '')}, SFXs: {len(level.sfx_ids or '')}")
            
        if level.upload_date and level.update_date:
            lines.append(f"Upload/update: {level.upload_date}/{level.update_date}")
        return lines
    
    def fetch_GDDL_backup(self):
        entries=GDDL_BACKUP.get_for_id(self.level_id)
        if entries:
            self.gddl_entry=entries[0]
        return self
    
    def set_GDDL(self,entry:GDDLLevel|None):
        self.gddl_entry=entry
        return self
    
    def set_gd_entry(self,entry:GDLevel|None,song:GDSong|None):
        self.gd_level=entry
        self.gd_song=song
        return self
    
def format_time(seconds:float) -> str:
    total_sec = round(seconds)
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s or not parts:
        parts.append(f"{s}s")
    return " ".join(parts)