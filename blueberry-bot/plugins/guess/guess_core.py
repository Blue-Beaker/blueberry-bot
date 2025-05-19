import json
import random
import os,sys
from . import utils

DATA_DIR="blueberry-bot/plugins/guess/data"
MAP_DATA_DIR="blueberry-bot/plugins/guess/map_export_data"

class GuessSession:
    map_name:str
    map_data:dict
    guesses:int
    revealed_info:dict
    entities:dict[str,int]
    
    def __init__(self,map_name:str,map_data:dict) -> None:
        print(map_data)
        self.map_name=map_name
        self.map_data=map_data
        self.entities=map_data['entities']
        self.guesses=0
        self.revealed_info={}
        pass
    
    def get_message(self)->str:
        return ""
    def do_guess(self,msg:str)->str:
        return ""

class GuessManager:
    session:GuessSession|None=None
    
    def get_session(self) -> GuessSession|None:
        return self.session
    
    def has_session(self) -> bool:
        if self.session:
            return True
        return False
        
    def start_guess(self) -> GuessSession:
        files = utils.listRecursive(MAP_DATA_DIR,".json")
        random_map=random.choice(files)
        with open(random_map) as f:
            map_data=json.load(f)
        self.session=GuessSession(os.path.relpath(random_map,MAP_DATA_DIR),map_data)
        return self.session