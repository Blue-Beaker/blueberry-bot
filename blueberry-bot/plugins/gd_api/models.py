
from abc import abstractmethod
from typing import get_type_hints

from nonebot import logger

class BaseLevel:
    def to_dict(self) -> dict:
        return self.__dict__
    def load_dict(self,data:dict):
        for key, target in get_type_hints(type(self)).items():
            value = data.get(key)
            if value is not None and target is not None:
                try:
                    value = target(value)
                except Exception as e:
                    logger.error(f"Failed loading value {value} -> {type(target)} in {self.__class__.__name__}: {e}")
                    value = getattr(type(self),key,None)
            else:
                value = getattr(type(self),key,None)
            self.__dict__[key] = value
        return self
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.load_dict(data)
        return inst
    
class LevelWithID(BaseLevel):
    @abstractmethod
    def get_id(self) -> int:
        pass