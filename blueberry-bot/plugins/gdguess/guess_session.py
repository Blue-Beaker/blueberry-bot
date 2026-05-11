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
        # 迁移 session_id 中的旧格式 key
        if "session_id" in data:
            data["session_id"] = migrate_single_key(data["session_id"])
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
                self.load_dict(migrate_entries_keys(data))
        except FileNotFoundError:
            self.entries={}
    

class SessionManager(BaseManager):
    entries:dict[str,GuessSession]={}
    save_path:str|None=None
    def __init__(self,save_path:str|None=None) -> None:
        self.entries={}
        self.save_path=save_path
            
    def get_or_create(self,id:str):
        entry=self.entries.get(id,None)
        if not entry:
            entry=GuessSession()
            self.entries[id]=entry
        return entry
    def to_dict(self):
        return {k:v.to_dict() for k,v in self.entries.items()}
    def load_dict(self,d:dict[str,dict]):
        self.entries={k:GuessSession.from_dict(v) for k,v in d.items()}

class ConfigManager(BaseManager):
    entries:dict[str,ConfigEntry]
    save_path:str|None=None
    
    def __init__(self,save_path:str|None=None) -> None:
        self.entries={}
        self.save_path=save_path
        
    def get_or_create(self,id:str,default_data:dict[str,Any]={}):
        cfg=self.entries.get(id,None)
        if not cfg:
            cfg=ConfigEntry.from_dict(default_data)
            self.entries[id]=cfg
        return cfg
    def to_dict(self):
        return {k:v.to_dict() for k,v in self.entries.items()}
    def load_dict(self,d:dict[str,dict]):
        self.entries={k:ConfigEntry.from_dict(v) for k,v in d.items()}


def migrate_entries_keys(data: dict[str, dict]) -> dict[str, dict]:
    """自动迁移旧格式 entries key 到当前格式（带下划线）。
    
    旧格式: dc<id> / group<id> / mc<name> / u<id>
    当前格式: dc_<id> / group_<id> / mc_<name> / u_<id>
    """
    migrated = {}
    for k, v in data.items():
        new_key = k
        if k.startswith("dc") and not k.startswith("dc_"):
            new_key = "dc_" + k[2:]
        elif k.startswith("group") and not k.startswith("group_"):
            new_key = "group_" + k[5:]
        elif k.startswith("mc") and not k.startswith("mc_"):
            new_key = "mc_" + k[2:]
        elif k.startswith("u") and not k.startswith("u_"):
            new_key = "u_" + k[1:]
        migrated[new_key] = v
    return migrated


def migrate_single_key(key: str) -> str:
    """迁移单个 ID key 从旧格式到当前格式（带下划线）。"""
    if key.startswith("dc") and not key.startswith("dc_"):
        return "dc_" + key[2:]
    if key.startswith("group") and not key.startswith("group_"):
        return "group_" + key[5:]
    if key.startswith("mc") and not key.startswith("mc_"):
        return "mc_" + key[2:]
    if key.startswith("u") and not key.startswith("u_"):
        return "u_" + key[1:]
    return key