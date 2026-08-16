from abc import abstractmethod
from typing import Type

class HigherLowerLevel:
    level_id:int=0
    placement:int=0
    name:str=""
    creator:str=""
    
    def get_id(self) -> int:
        return self.level_id
        
    def get_placement(self) -> int:
        return self.placement
    
    def get_repr(self) -> str:
        return f"{self.name}{' by '+self.creator if self.creator else ''} ({self.level_id})"
    
    def to_dict(self) -> dict:
        return self.__dict__
    
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.__dict__.update(data)
        return inst
    
class LevelProvider:
    @abstractmethod
    async def getLevels(self,params:str) -> list[HigherLowerLevel]:
        pass