from typing import override
from nonebot import require
from .basic_models import BaseSerializableEntry,GenericLevelEntry

require('gd_api')
from ...gd_api import gddl,aredl,pemonlist,platformerlist
    
class GDDLLevel(gddl.GDDLLevel,BaseSerializableEntry):
    def __init__(self,level:gddl.GDDLLevel) -> None:
        super().__init__()
        self.__dict__.update(level.__dict__)
    @override
    def getID(self):
        return self.ID
    
class AREDLLevel(aredl.Level,BaseSerializableEntry):
    def __init__(self,level:aredl.Level) -> None:
        super().__init__()
        self.__dict__.update(level.__dict__)
    @override
    def getID(self):
        return self.level_id
    
class PemonlistLevel(pemonlist.Level,GenericLevelEntry[pemonlist.Level]):
    @override
    def getID(self):
        return self.get_id()
    
class TPLLevel(platformerlist.Level,GenericLevelEntry[platformerlist.Level]):
    @override
    def getID(self):
        return self.get_id()
    

