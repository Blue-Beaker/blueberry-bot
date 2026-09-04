from enum import Enum
from types import NoneType, UnionType
from typing import Any, Generic, TypeVar, get_type_hints, override
from nonebot import get_driver, logger,require
require('gd_api')
from ..gd_api import gd,thumbs,gddl,aredl,pemonlist,platformerlist

class BaseSerializableEntry:
    def getID(self) -> int:
        return -1
    def to_dict(self) -> dict:
        data={}
        
        for k,v in self.__dict__.items():
            def_value=getattr(self.__class__,k,None)
            if v==None and def_value==None:
                continue
            if isinstance(v,Enum):
                v=v.value
            data[k]=v
        return data
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        for k,v in data.items():
            adapt_variable(inst,k,v)
        # inst.__dict__.update(data)
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
    


def adapt_variable(inst,key:str,value:Any):
    if value is None:
        return
    targets=[]
    type_hint=get_type_hints(type(inst)).get(key,None)
    if isinstance(type_hint,UnionType):
        targets.extend(type_hint.__args__)
    elif type_hint is not None:
        targets.append(type_hint)
    
    fitted=False
    errors=[]
        
    for target in targets:
        try:
            if target==NoneType:
                if value==None:
                    fitted=True
                    break
                continue
            value=target(value)
            fitted=True
            break
        except Exception as e:
            errors.append(e)
    if (not fitted) and errors:
        logger.error(f"Failed loading value {value} -> {target} in {inst.__class__.__name__}: {errors}")
    inst.__dict__[key]=value