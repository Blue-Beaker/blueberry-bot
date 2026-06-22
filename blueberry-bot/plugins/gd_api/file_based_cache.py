import json
import os,sys
from pathlib import Path
import time
import traceback
from typing import Callable, Generic, Literal, TypeVar, cast
from nonebot import logger

_D = TypeVar("_D")

class FileBasedCache(Generic[_D]):
    cache_path:Path|Literal['']|None=None
    expiration:float=3600
    data_type:type[_D]
    updateFunction:Callable[[],_D]
    cache_name:str="cache"
    
    failure_cooldown:float=300
    fail_try_time:float=0
    
    def __init__(self,data_type:type[_D],updateFunction:Callable[[],_D],cache_path:str|Path|None=None,expiration:float=3600,cache_name:str="cache") -> None:
        self.data_type=data_type
        self.updateFunction=updateFunction
        self.expiration=expiration
        self.cache_path=Path(os.path.abspath(cache_path)) if cache_path else cache_path
        self.cache_name=cache_name
        self.fail_try_time:float=0
    
    def shouldUpdate(self) -> bool:
        if time.time()<self.fail_try_time:
            return False
        if not self.cache_path:
            return True
        if not self.cache_path.exists():
            return True
        if self.cache_path.stat().st_size == 0:
            return True
        
        
        mtime=os.stat(self.cache_path).st_mtime
        return time.time()-mtime>self.expiration
    
    def update(self,data:_D) -> bool:
        if not self.cache_path:
            return False
        if data is None:
            return False
        
        self.cache_path.parent.mkdir(exist_ok=True)
        
        if isinstance(data,str):
            with open(self.cache_path,"w") as f:
                f.write(data)
        elif isinstance(data,bytes):
            with open(self.cache_path,"wb") as f:
                f.write(data)
        else:
            with open(self.cache_path,"w") as f:
                json.dump(data,f)
        self.fail_try_time=0
        return True
    
    def get(self) -> _D|None:
        if not self.cache_path:
            return None
        
        if self.data_type==str:
            with open(self.cache_path,"r") as f:
                return cast(_D, f.read())
        elif self.data_type==bytes:
            with open(self.cache_path,"rb") as f:
                return cast(_D, f.read())
        else:
            with open(self.cache_path,"r") as f:
                return json.load(f)
            
    def updateNow(self):
        try:
            data=self.updateFunction()
            if data:
                self.update(data)
                return cast(_D,data)
            else:
                self.fail_try_time=time.time()+self.failure_cooldown
        except Exception as e:
            logger.error(f"Error updating {self.cache_name}: {traceback.format_exc()}")
            self.fail_try_time=time.time()+self.failure_cooldown
            
        return cast(_D,self.get())
        
    def getOrUpdate(self):
        if self.shouldUpdate():
            logger.info(f"Updating {self.cache_name}...")
            try:
                data=self.updateFunction()
                if data:
                    self.update(data)
                    return cast(_D,data)
                else:
                    self.fail_try_time=time.time()+self.failure_cooldown
            except Exception as e:
                logger.error(f"Error updating {self.cache_name}: {traceback.format_exc()}")
                self.fail_try_time=time.time()+self.failure_cooldown
                
        return cast(_D,self.get())