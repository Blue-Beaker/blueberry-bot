import json
import os
from typing import Any


class OrbStorage:
    balances:dict[str,int]
    config_path:str|None
    
    def __init__(self,config_path:str|None=None) -> None:
        self.balances={}
        self.config_path=config_path
    
    def to_dict(self):
        return {"balances":self.balances,"version":1}
    
    def load_dict(self,data:dict[str,Any]):
        self.balances=data.get("balances",self.balances)
        
        
    def save(self) -> None:
        if not self.config_path:
            return
        
        data = self.to_dict()
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> None:
        if not self.config_path or not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(data, dict):
            return
        self.load_dict(data)
        
        
    def get_balance(self,user:str):
        return self.balances.get(user,0)
    
    def add_balance(self,user:str,count:int,allow_negative:bool=False):
        changed=self.get_balance(user)+count
        if(not allow_negative and count<0 and changed<0):
            return False
        self.balances[user]=changed
        return True