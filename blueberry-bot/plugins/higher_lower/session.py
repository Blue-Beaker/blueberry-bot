from enum import Enum
import json
import random
from .models import HigherLowerLevel

class HigherLowerSession:
    levels:list[HigherLowerLevel]
    streak:int=0
    picked_levels:list[HigherLowerLevel]
    finished:bool=True
    
    def __init__(self) -> None:
        self.levels=[]
        self.picked_levels=[]
    
    def start(self,levels:list[HigherLowerLevel]):
        self.streak=0
        self.finished=False
        self.levels=[]
        self.picked_levels=[]
        
        self.levels=levels.copy()
        self.choice()
        self.choice()
        return True
    
    def choice(self):
        pool=set(self.levels)
        if self.picked_levels.__len__()>0:
            pool.remove(self.picked_levels[-1])
        l=random.choice(list(pool))
        self.picked_levels.append(l)
    
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
        return {"levels": [l.get_id() for l in self.levels],
                "streak": self.streak,
                "picked_levels": [l.get_id() for l in self.picked_levels]
                }
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        
        inst.streak=data.get("streak",0)
        
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