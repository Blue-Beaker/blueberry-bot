from typing import override
from nonebot import get_driver,require
require('gd_api')
from ..gd_api import gd,thumbs,gddl,aredl,pemonlist

class BaseLevelEntry:
    def getID(self) -> int:
        return -1
    def to_dict(self) -> dict:
        return self.__dict__
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.__dict__.update(data)
        return inst
    
class GDDLLevel(gddl.GDDLLevel,BaseLevelEntry):
    def __init__(self,level:gddl.GDDLLevel) -> None:
        super().__init__()
        self.__dict__.update(level.__dict__)
    @override
    def getID(self):
        return self.ID
    
class AREDLLevel(aredl.Level,BaseLevelEntry):
    def __init__(self,level:aredl.Level) -> None:
        super().__init__()
        self.__dict__.update(level.__dict__)
    @override
    def getID(self):
        return self.level_id
    
class PemonlistLevel(pemonlist.Level,BaseLevelEntry):
    def __init__(self,level:pemonlist.Level) -> None:
        super().__init__()
        self.__dict__.update(level.__dict__)
    @override
    def getID(self):
        return self.level_id