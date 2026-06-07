import json
import os
from pathlib import Path
from typing import Any


class GusEntry:
    file:str
    name:str
    desc:str
    def update(self,data:dict[str,str]):
        self.__dict__.update(data)
        return self
    def __repr__(self) -> str:
        return f"GusEntry:{self.__dict__}"
    
class GusData:
    entries:dict[str,GusEntry]
    config_path:str
    entries_path:Path
    
    def __init__(self,config_path:str|Path,entries_path:str|Path) -> None:
        self.entries={}
        self.config_path=os.path.abspath(config_path)
        self.entries_path=Path(entries_path).absolute()
        
    def to_dict(self):
        data={}
        data["entries"]={k:e.__dict__ for k,e in self.entries.items()}
        return data
    
    def load_dict(self,data:dict[str,Any]):
        entries=data.get("entries",{})
        if isinstance(entries,dict):
            self.entries={}
            for k,e in entries.items():
                entry=GusEntry().update(e)
                self.entries[k]=entry
        return self
    
    def load(self):
        try:
            with open(self.config_path,"r") as f:
                data=json.load(f)
                self.load_dict(data)
        except FileNotFoundError:
            self.entries={}
            
    def save(self):
        with open(self.config_path,"w") as f:
            json.dump(self.to_dict(),f,ensure_ascii=False)
            
    def get_entries(self):
        return self.entries

    def get_img(self,key:str) -> bytes|None:
        entry=self.entries.get(key)
        if not entry:
            return None
        
        filepath=self.entries_path/entry.file
        try:
            with open(filepath,"rb") as f:
                return f.read()
        except:
            return None
        return None
    
    def get_data(self,key:str):
        return self.entries.get(key)
    
    def add_entry(self,key:str,entry:GusEntry,image:bytes):
        
        self.entries[key]=entry
        
        filepath=self.entries_path/entry.file
        
        self.entries_path.mkdir(parents=True,exist_ok=True)
        
        with open(filepath,"wb") as f:
            f.write(image)
            
    def remove_entry(self,key:str):
        entry=self.get_data(key)
        if not entry:
            return False
        filepath=self.entries_path/entry.file
        os.remove(filepath)
        self.entries.pop(key)
        return entry