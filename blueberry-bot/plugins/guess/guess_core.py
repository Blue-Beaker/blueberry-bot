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
    
    def get_unrevealed_entity(self):
        choices:list[tuple[EntityCategory,int]]=[]
        for c in self.categorized_entities.items():
            if c[0] not in self.revealed_info.keys():
                choices.append(c)
        return choices
    
    def get_info(self)->tuple[EntityCategory,int]:
        choice=random.choice(self.get_unrevealed_entity())
        return (choice[0],choice[1])
    
    def reveal_info(self):
        k,v=self.get_info()
        self.revealed_info[k]=v
    
    def get_message_from_revealed_info(self,k:EntityCategory,v:int)->str:
        return f"{k.name}的数量为{v}"
    
    def get_final_message(self):
        messageLines=[]
        for k,v in self.revealed_info.items():
            messageLines.append(self.get_message_from_revealed_info(k,v))
        return "\n".join(messageLines)
    
    def do_guess(self,msg:str)->str:
        map=guess_data.MAP_MANAGER.get_map_from_alias(msg.strip())
        # if(not map):
        #     return "你输入的地图不存在! 请输入正确的地图名或别称"
        if(msg==self.map_name or map==self.map_name):
            return "你猜对了!"
        else:
            if(self.get_unrevealed_entity().__len__()>0):
                self.reveal_info()
            return self.get_final_message()
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