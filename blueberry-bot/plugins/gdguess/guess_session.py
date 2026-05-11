import json
from typing import Any
from .gd_api import Level

class GuessSession:
    session_id:str
    level_id:int
    level_name:str
    level_creator:str
    
    guesses:int
    
    crop:tuple[int,int,int,int]
    
    level_pool:list[int]
    
    completed:bool=False
    
    def __init__(self) -> None:
        self.level_pool=[]
        self.completed=False
        self.guesses=0
        
    def start(self,session_id:str,level:Level,crop:tuple[int,int,int,int],level_pool:list[int]=[]):
        self.session_id=session_id
        self.level_id=level.id
        self.level_name=level.name
        self.level_creator=level.creator
        self.guesses=0
        self.crop=crop
        self.level_pool=level_pool
        self.completed=False
        return self
    
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

class ConfigEntry:
    cooldown:int=10
    def __str__(self) -> str:
        return f"guess冷却: {self.cooldown}s"
    def to_dict(self) -> dict:
        return self.__dict__
    @classmethod
    def from_dict(cls,data:dict):
        inst=cls()
        inst.__dict__.update(data)
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
    sessions:dict[str,GuessSession]={}
    save_path:str|None=None
    def __init__(self,save_path:str|None=None) -> None:
        self.sessions={}
        self.save_path=save_path
            
    def to_dict(self):
        return {k:v.to_dict() for k,v in self.sessions.items()}
    def load_dict(self,d:dict[str,dict]):
        self.sessions={k:GuessSession.from_dict(v) for k,v in d.items()}

class ConfigManager(BaseManager):
    entries:dict[str,ConfigEntry]
    save_path:str|None=None
    
    def __init__(self,save_path:str|None=None) -> None:
        self.entries={}
        self.save_path=save_path
        
    def get(self,id:str,default_data:dict[str,Any]={}):
        cfg=self.entries.get(id,None)
        if not cfg:
            cfg=ConfigEntry.from_dict(default_data)
            self.entries[id]=cfg
        return cfg
    def to_dict(self):
        return {k:v.to_dict() for k,v in self.entries.items()}
    def load_dict(self,d:dict[str,dict]):
        self.entries={k:ConfigEntry.from_dict(v) for k,v in d.items()}