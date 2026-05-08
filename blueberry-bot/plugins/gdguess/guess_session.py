import json
from .gd_api import Level

class GuessSession:
    session_id:str
    level_id:int
    level_name:str
    level_creator:str
    
    guesses:int
    
    crop:tuple[int,int,int,int]
    
    level_pool:list[int]
    
    def __init__(self) -> None:
        self.level_pool=[]
        
    @classmethod
    def start(cls,session_id:str,level:Level,crop:tuple[int,int,int,int],level_pool:list[int]=[]):
        inst=cls()
        inst.session_id=session_id
        inst.level_id=level.id
        inst.level_name=level.name
        inst.level_creator=level.creator
        inst.guesses=0
        inst.crop=crop
        inst.level_pool=level_pool
        return inst
    
    def guess(self,guess:str):
        self.guesses+=1
        return guess.strip().lower()==self.level_name.strip().lower()
    
    def to_dict(self) -> dict:
        return self.__dict__
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.__dict__.update(data)
        return inst