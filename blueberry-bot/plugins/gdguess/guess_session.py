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
    
class SessionManager:
    sessions:dict[str,GuessSession]={}
    
    def save(self,path:str):
        with open(path,"w") as f:
            json.dump({k:v.to_dict() for k,v in self.sessions.items()},f)
    
    def load(self,path:str):
        try:
            with open(path,"r") as f:
                data=json.load(f)
                self.sessions={k:GuessSession.from_dict(v) for k,v in data.items()}
        except FileNotFoundError:
            self.sessions={}
