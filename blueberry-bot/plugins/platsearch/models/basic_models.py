from enum import Enum
import re
from types import NoneType, UnionType
from typing import Any, Generic, TypeVar, get_type_hints, override
from nonebot import logger

from enum import Enum
from typing import Generic, TypeVar


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
    
BASENAME_REGEX = re.compile(r"(.*)\((.*)\)")
class LevelEntry(BaseSerializableEntry):
    id:int=0
    name:str
    
    @override
    def getID(self) -> int:
        return self.id
    def exactMatch(self,search:str):
        return search.lower().replace("(","").replace(")","").strip() == self.name.lower().replace("(","").replace(")","").strip()
    def matchesName(self,search:str,fuzzy_match:bool=False):
        if self.exactMatch(search):
            return True
        if fuzzy_match:
            return search.lower() in self.name.lower()
        else:
            matched=BASENAME_REGEX.match(self.name)
            name=self.name
            if matched:
                name=matched.group(1)
            return search.lower().strip() == name.lower().strip()
    def nameKey(self):
        return self.name.lower().strip()
    
_L = TypeVar("_L")
    
class GenericLevelEntry(BaseSerializableEntry,Generic[_L]):
    def __init__(self,level:_L) -> None:
        super().__init__()
        self.__dict__.update(level.__dict__)
        
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