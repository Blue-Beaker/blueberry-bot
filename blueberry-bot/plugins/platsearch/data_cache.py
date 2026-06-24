import time
import traceback
from typing import Callable, Generic, Sequence, Type,TypeVar
from .plat_sheets import PlatWeight, TheListsEntry,LevelEntry
import json
from nonebot import logger

_T = TypeVar("_T",covariant=True, bound=LevelEntry)
    
class BaseCache(Generic[_T]):
    expiration_time:int
    entries:list[_T]
    entry_type:Type[_T]
    ttl:int=3600
    
    update_function:Callable[[],list[_T]]
    file_path:str|None
    
    def __init__(self,t:Type[_T],file_path:str|None=None,ttl:int=3600) -> None:
        self.expiration_time=0
        self.entries=[]
        self.entry_type=t
        
        self.ttl=ttl
        self.file_path=file_path
    
    def to_dict(self) -> dict:
        result={"expiration_time":self.expiration_time,"entries":[e.to_dict() for e in self.entries]}
        return result
    
    def set_update_function(self,func:Callable[[],list[_T]]):
        self.update_function=func
        return self
    
    def should_update(self) -> bool:
        now=int(time.time())
        return now>self.expiration_time
        
    def update(self):
        if hasattr(self,"update_function"):
            try:
                result=self.update_function()
                if result.__len__()>0:
                    self.entries=result
                    self.expiration_time=int(time.time())+self.ttl
                    if self.file_path:
                        self.save(self.file_path)
                else:
                    logger.warning("Failed to update cache, got empty data")
            except Exception as e:
                logger.error(f"Error while updating cache: {e}")
                logger.debug("Traceback:",traceback.format_exc())
        else:
            logger.warning("No update function set for cache")
            
    def get(self) -> list[_T]:
        if self.expiration_time==0 and self.file_path:
            self.load(self.file_path)
        
        if self.should_update():
            logger.info("Cache expired, updating...")
            self.update()
        return self.entries
    
    @classmethod
    def from_dict(cls,t,data:dict):
        inst=cls(t)
        inst.__dict__.update(data)
        return inst
    
    def load(self,path:str):
        try:
            with open(path,"r") as f:
                data=json.load(f)
                self.entries=[self.entry_type.from_dict(e) for e in data.get("entries",[])]
                self.expiration_time=data.get("expiration_time",0)
        except FileNotFoundError:
            self.entries=[]
            self.expiration_time=0
            
    def save(self,path:str):
        with open(path,"w") as f:
            json.dump(self.to_dict(),f)

class IDMapCache(Generic[_T]):
    def __init__(self) -> None:
        super().__init__()
        self.id_map:dict[int,list[_T]]={}
    def update_data(self,entries:Sequence[_T]):
        self.id_map.clear()
        for e in entries:
            if e.id not in self.id_map:
                self.id_map[e.id]=[]
            self.id_map[e.id].append(e)
    def get_for_id(self,id:int):
        return self.id_map.get(id,[])
    
class ManagedIDMapCache(IDMapCache[_T]):
    last_expiration_time:int=0
    def __init__(self,parent_cache:BaseCache[_T]) -> None:
        super().__init__()
        self.parent=parent_cache
    def try_update(self):
        if (self.parent.should_update()
            or self.last_expiration_time<self.parent.expiration_time):
            self.update_data(self.parent.get())
        self.last_expiration_time=self.parent.expiration_time
    def get_for_id(self, id: int):
        self.try_update()
        return super().get_for_id(id)