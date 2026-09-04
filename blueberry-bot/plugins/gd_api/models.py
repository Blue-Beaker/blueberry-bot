
from abc import abstractmethod
from enum import Enum
from types import NoneType, UnionType
from typing import Any, get_type_hints
from nonebot import logger
    
class BaseAdaptingModel:
    def adapt_variable(self,key:str,value:Any):
        if value is None:
            return
        targets=[]
        type_hint=get_type_hints(type(self)).get(key,None)
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
            logger.error(f"Failed loading value {value} -> {target} in {self.__class__.__name__}: {errors}")
        self.__dict__[key]=value
        
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
    
    def load_dict(self,data:dict):
        for k,v in data.items():
            self.adapt_variable(k,v)
        return self
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.load_dict(data)
        return inst
    
class LevelWithID(BaseAdaptingModel):
    @abstractmethod
    def get_id(self) -> int:
        pass