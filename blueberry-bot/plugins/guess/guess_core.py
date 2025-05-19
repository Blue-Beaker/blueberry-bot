import json
import random
import os,sys
from . import utils,guess_data
from .guess_data import EntityCategory,MapData

MAP_DATA_DIR="blueberry-bot/plugins/guess/map_export_data"

class GuessSession:
    map_name:str
    mapData:MapData
    map_jsondata:dict
    guesses:int
    revealed_info:dict
    entities:dict[str,int]
    
    def __init__(self,map_name:str,map_data:dict) -> None:
        self.map_name=map_name
        self.map_jsondata=map_data
        self.entities=map_data['entities']
        self.guesses=0
        self.revealed_info={}
        self.categorized_entities:dict[EntityCategory,int]={}
        self.count_categories()
        print(f"{self.map_name}:\n{self.categorized_entities}\n{self.entities}")
        
    def count_categories(self):
        for entity in self.entities:
            for category in guess_data.ENTITY_MANAGER.get_categories(entity):
                if(category not in self.categorized_entities.keys()):
                    self.categorized_entities[category]=self.entities[entity]
                else:
                    self.categorized_entities[category]=self.categorized_entities[category]+self.entities[entity]
        
    def get_info(self)->tuple[EntityCategory,str]:
        choice=random.choice(list(self.categorized_entities.items()))
        return (choice[0],str(choice[1]))
    
    def reveal_info(self)->str:
        k,v=self.get_info()
        self.revealed_info[k]=v
        return f"{k.name}的数量为{v}"
    
    def do_guess(self,msg:str)->str:
        map=guess_data.MAP_MANAGER.get_map_from_alias(msg.strip())
        # if(not map):
        #     return "你输入的地图不存在! 请输入正确的地图名或别称"
        if(msg==self.map_name or map==self.map_name):
            return "你猜对了!"
        else:
            return self.reveal_info()
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
    
if __name__ == '__main__':
    manager=GuessManager()
    session=manager.start_guess()
    print(session.map_name, session.categorized_entities)