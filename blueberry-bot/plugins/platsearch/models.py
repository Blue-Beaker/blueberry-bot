from typing import Generic, TypeVar, override
from nonebot import get_driver,require
require('gd_api')
from ..gd_api import gd,thumbs,gddl,aredl,pemonlist,platformerlist

class BaseSerializableEntry:
    def getID(self) -> int:
        return -1
    def to_dict(self) -> dict:
        data=self.__dict__.copy()
        
        for k,v in self.__dict__.items():
            def_value=getattr(self.__class__,k,None)
            if v==None and def_value==None:
                data.pop(k,None)
                
        return data
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.__dict__.update(data)
        return inst
    
_L = TypeVar("_L")
    
class GenericLevelEntry(BaseSerializableEntry,Generic[_L]):
    def __init__(self,level:_L) -> None:
        super().__init__()
        self.__dict__.update(level.__dict__)
    
    
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