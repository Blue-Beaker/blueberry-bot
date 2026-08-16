
from abc import abstractmethod
from enum import Enum
from typing import override
from .models import HigherLowerLevel,LevelProvider

from nonebot import require
require("gd_api")
from ..gd_api.pemonlist import getPemonlistLevels_async, Level as PemonlistLevel
from ..gd_api.aredl import getAREDLLevels_async, Level as AREDLLevel

class GuessAction(Enum):
    GUESS="guess"
    START="start"
    GIVEUP="giveup"
    HELP="help"
class GuessSource(Enum):
    LAST="last"
    PEMONLIST="pemonlist"
    AREDL="aredl"
    AREPL="arepl"
    
PROVIDERS:dict[GuessSource,LevelProvider]={}
    
class GuessArgs:
    action:GuessAction
    source:GuessSource
    def __init__(self,text:str) -> None:
        self.action=GuessAction.GUESS
        self.source=GuessSource.PEMONLIST
        
        args=text.split(" ")
        
        while args and args[0].startswith("-"):
            arg=args[0].removeprefix("-")
            args.pop(0)
            self.applyArg(arg)
            
        self.text=" ".join(args)
            
    def applyArg(self,arg:str):
        if arg in GuessAction:
            self.action=GuessAction(arg)
            return
        if arg in GuessSource:
            self.action=GuessAction.START
            self.source=GuessSource(arg)
            
    def getProvider(self):
        return PROVIDERS.get(self.source)


class PemonlistLevelProvider(LevelProvider):
    @override
    async def getLevels(self, params: str) -> list[HigherLowerLevel]:
        levels = await getPemonlistLevels_async()
        if not levels:
            return []
        return [self.convertLevel(l) for l in levels]
    
    def convertLevel(self,l:PemonlistLevel):
        hll=HigherLowerLevel()
        hll.level_id=l.level_id
        hll.name=l.name
        hll.creator=l.creator
        hll.placement=l.placement
        return hll
    
class AREDLLevelProvider(LevelProvider):
    def __init__(self,is_plat:bool=False) -> None:
        super().__init__()
        self.is_plat=is_plat
    @override
    async def getLevels(self, params: str) -> list[HigherLowerLevel]:
        levels = await getAREDLLevels_async(self.is_plat)
        if not levels:
            return []
        return [self.convertLevel(l) for l in levels]
    
    def convertLevel(self,l:AREDLLevel):
        hll=HigherLowerLevel()
        hll.level_id=l.level_id
        hll.name=l.name
        hll.creator=""
        hll.placement=l.position
        return hll
    
PROVIDERS[GuessSource.PEMONLIST]=PemonlistLevelProvider()
PROVIDERS[GuessSource.AREDL]=AREDLLevelProvider(False)
PROVIDERS[GuessSource.AREPL]=AREDLLevelProvider(True)