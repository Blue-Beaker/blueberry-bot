from enum import Enum
import json
import random
from typing import get_type_hints

from nonebot import logger
from .models import HigherLowerLevel

class HigherLowerSession:
    levels:dict[int,HigherLowerLevel]
    streak:int=0
    picked_levels:list[HigherLowerLevel]
    finished:bool=True
    last_source:str='pemonlist'
    
    def __init__(self) -> None:
        self.levels={}
        self.picked_levels=[]
    
    def start(self,levels:list[HigherLowerLevel]):
        self.streak=0
        self.finished=False
        self.levels={}
        self.picked_levels=[]
        
        self.levels={l.get_id():l for l in levels}
        self.choice()
        self.choice()
        return True
    
    def choice(self):
        pool=set(self.levels.keys())
        if self.picked_levels.__len__()>0:
            lastID=self.picked_levels[-1].get_id()
            if lastID in pool:
                pool.remove(lastID)
        newID=random.choice(list(pool))
        self.picked_levels.append(self.levels[newID])
    
    def getLastLevels(self):
        if self.picked_levels.__len__()>=2:
            return self.picked_levels[-2],self.picked_levels[-1]
    
    def do_guess(self,guess:int=0) -> bool:
        levels=self.getLastLevels()
        if not levels:
            return False
        
        placement_delta=levels[0].get_placement()-levels[1].get_placement()
        return guess*placement_delta>0 # guess>0 and placement_delta>0, or guess<0 and placement_delta<0
    
    def to_dict(self) -> dict:
        data = {}
        for k,v in self.__dict__.items():
            if k == "levels":
                data[k]=[l.to_dict() for l in v.values()]
            elif k == "picked_levels":
                data[k]=[l.to_dict() for l in v]
            else:
                data[k]=v
        return data
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        type_hints=get_type_hints(cls)
        for key,value in data.items():
            if key in ["levels","picked_levels"]:
                continue
            
            target=type_hints.get(key)
            if value is not None and target is not None:
                try:
                    inst.__dict__[key] = target(value)
                except Exception as e:
                    logger.error(f"Failed loading value {value} -> {type(target)} in {cls.__name__}: {e}")
                    inst.__dict__[key] = getattr(cls,key,None)
            else:
                inst.__dict__[key] = getattr(cls,key,None)
                
        inst.levels = {}
        for l in data.get("levels",[]):
            level=HigherLowerLevel.from_dict(l)
            inst.levels[level.get_id()]=level
        inst.picked_levels = [HigherLowerLevel.from_dict(l) for l in data.get("picked_levels",[])]
        
        return inst
    
class BaseManager:
    save_path:str|None=None
    
    def to_dict(self):
        return {}
    def load_dict(self,d:dict[str,dict]):
        pass
    def save(self):
        if not self.save_path:
            return
        with open(self.save_path,"w") as f:
            json.dump(self.to_dict(),f)
    
    def load(self):
        if not self.save_path:
            return
        try:
            with open(self.save_path,"r") as f:
                data=json.load(f)
                self.load_dict(data)
        except FileNotFoundError:
            self.entries={}
    
class SessionManager(BaseManager):
    entries:dict[str,HigherLowerSession]={}
    save_path:str|None=None
    def __init__(self,save_path:str|None=None) -> None:
        self.entries={}
        self.save_path=save_path
            
    def get_or_create(self,id:str):
        entry=self.entries.get(id,None)
        if not entry:
            entry=HigherLowerSession()
            self.entries[id]=entry
        return entry
    def to_dict(self):
        return {k:v.to_dict() for k,v in self.entries.items()}
    def load_dict(self,d:dict[str,dict]):
        self.entries={k:HigherLowerSession.from_dict(v) for k,v in d.items()}