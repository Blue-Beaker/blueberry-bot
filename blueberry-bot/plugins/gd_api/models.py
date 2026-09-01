
from abc import abstractmethod
from typing import Any, get_type_hints
from nonebot import logger
    
class BaseAdaptingModel:
    def adapt_variable(self,key:str,value:Any):
        if value is None:
            return
        target=get_type_hints(type(self)).get(key,None)
        if target:
            try:
                value=target(value)
            except Exception as e:
                logger.error(f"Failed loading value {value} -> {target} in {self.__class__.__name__}: {e}")
        self.__dict__[key]=value
        
    def to_dict(self) -> dict:
        return self.__dict__.copy()
    
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