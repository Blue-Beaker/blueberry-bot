import time
import traceback
from typing import Any, Callable, Generic, Sequence, Type,TypeVar, override
from .models import BaseSerializableEntry
import json
from nonebot import logger

_TA = TypeVar("_TA", covariant=True)
_T = TypeVar("_T", covariant=True, bound=BaseSerializableEntry)
_K = TypeVar("_K")
    
class BaseCache(Generic[_T]):
    expiration_time:int
    entries:list[_T]
    entry_type:Type[_T]
    ttl:int=3600
    
    update_function:Callable[[],list[_T]]
    file_path:str|None
    
    name:str=""
    
    post_refresh_functions:list[Callable[[],Any]]
    
    def __init__(self,t:Type[_T],file_path:str|None=None,ttl:int=3600,name:str="UNNAMED") -> None:
        self.expiration_time=0
        self.entries=[]
        self.entry_type=t
        
        self.ttl=ttl
        self.file_path=file_path
        self.name=name
        self.post_refresh_functions=[]
    
    def to_dict(self) -> dict:
        result={"expiration_time":self.expiration_time,"entries":[e.to_dict() for e in self.entries]}
        return result
    
    def set_update_function(self,func:Callable[[],list[_T]]):
        self.update_function=func
        return self
    
    def should_update(self) -> bool:
        now=int(time.time())
        return now>self.expiration_time
    
    def _post_update(self):
        for f in self.post_refresh_functions:
            try:
                f()
            except Exception as e:
                logger.error(f"Error running post-update function {f} in {self.name}: {e}")
        
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
                    logger.warning(f"Failed to update cache [{self.name}], got empty data")
                self._post_update()
            except Exception as e:
                logger.error(f"Error while updating cache [{self.name}]: {e}")
                logger.debug("Traceback:",traceback.format_exc())
        else:
            logger.warning(f"No update function set for cache [{self.name}]")
            
    def getOrUpdate(self) -> list[_T]:
        self.loadWhenNeeded()
        
        if self.should_update():
            logger.info(f"[{self.name}]: Cache expired, updating...")
            self.update()
        return self.entries
    
    def get(self) -> list[_T]:
        self.loadWhenNeeded()
        return self.entries
    
    def loadWhenNeeded(self):
        if self.expiration_time==0 and self.file_path:
            self.load(self.file_path)
            self._post_update()
    
    def getLogInfo(self):
        return f"[{self.name}]: {self.entries.__len__()} entries, expiring at {time.ctime(self.expiration_time)}"
    
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

class BaseCacheWithMaps(BaseCache[_T]):
    keymaps:list["KeyMapCache[_T,Any]"]
    def __init__(self, t: type[_T], file_path: str | None = None, ttl: int = 3600, name: str = "UNNAMED") -> None:
        super().__init__(t, file_path, ttl, name)
        self.keymaps=[]
        self.post_refresh_functions.append(self.update_keymaps)
    
    def add_keymap(self,map_cache:"KeyMapCache[_T,Any]"):
        self.keymaps.append(map_cache)
        
    def update_keymaps(self):
        for map in self.keymaps:
            map.update_data(self.entries)

class KeyMapCache(Generic[_TA,_K]):
    def __init__(self,key_getter:Callable[[_TA],_K]) -> None:
        super().__init__()
        self.key_getter=key_getter
        self.map:dict[_K,list[_TA]]={}
    def update_data(self,entries:Sequence[_TA]):
        self.map.clear()
        for e in entries:
            key=self.key_getter(e)
            if key not in self.map:
                self.map[key]=[]
            self.map[key].append(e)
    def get(self,id:_K):
        return self.map.get(id,[])
    
class IDMapCache(KeyMapCache[_T,int]):
    def __init__(self) -> None:
        super().__init__(IDMapCache.get_serializable_id)
    def get_for_id(self,id:int):
        return super().get(id)
    @staticmethod
    def get_serializable_id(entry:BaseSerializableEntry):
        return entry.getID()
    
class CacheWithIDMap(BaseCacheWithMaps[_T]):
    def __init__(self, t: type[_T], file_path: str | None = None, ttl: int = 3600, name: str = "UNNAMED") -> None:
        super().__init__(t, file_path, ttl, name)
        self.id_map:IDMapCache[_T]=IDMapCache()
        self.keymaps.append(self.id_map)
    def get_for_id(self,id:int):
        return self.id_map.get_for_id(id)
        
        