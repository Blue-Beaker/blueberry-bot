import json
import random
import os,sys
from . import utils,guess_data
from .guess_data import EntityCategory,MapData

MAP_DATA_DIR="blueberry-bot/plugins/guess/map_export_data"

class GuessSession:
    
    @property
    def map_name(self):
        return self.mapData.name
    @property
    def aliases(self):
        return self.mapData.aliases
    
    mapData:MapData
    map_jsondata:dict
    guesses:int
    revealed_info:dict
    entities:dict[str,int]
    
    def __init__(self,mapData:MapData,map_data:dict) -> None:
        self.mapData=mapData
        
        self.guesses=0
        self.revealed_info={}
        self.finished=False
        
        self.map_jsondata=map_data
        self.entities=map_data['entities']
        self.count_categories()
        print(f"{self.map_name}:\n{self.categorized_entities}\n{self.entities}")
    
    def count_categories(self):
        self.categorized_entities:dict[EntityCategory,int]={}
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
        msg=msg.strip()
        print(msg)
        map=guess_data.MAP_MANAGER.get_map_from_alias(msg)
        if(not map):
            return "没有找到你输入的地图! 请输入正确的地图名或别称"
        if(map==self.map_name or msg in self.aliases):
            self.finished=True
            return f"你猜对了! 正确答案是: {self.map_name}"
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
    
    def _start_guess(self) -> GuessSession:
        # files = utils.listRecursive(MAP_DATA_DIR,".json")
        # random_map=random.choice(files)
        
        map=guess_data.MAP_MANAGER.pickMap()
        random_map=os.path.join(MAP_DATA_DIR,map.filePath)
        
        with open(random_map) as f:
            map_data=json.load(f)
            
        self.session=GuessSession(map,map_data)
        return self.session
    
    def start(self)->str:
        if(self.session):
            return "当前有正在进行的guess 请先猜出来"
        self.session=self._start_guess()
        self.session.reveal_info()
        return self.session.get_final_message()
    
    def cancel(self)->str:
        if(not self.session):
            return "当前没有正在进行的guess"
        session=self.session
        self.session=None
        return f"你放弃了! 答案是: {session.map_name}"
    
    def do_guess(self,msg:str) -> str:
        if(not self.session):
            return "当前没有正在进行的guess 请&guess start开始猜图"
        result=self.session.do_guess(msg)
        if(self.session.finished):
            self.session=None
        return result
        
        
    
if __name__ == '__main__':
    manager=GuessManager()
    session=manager._start_guess()
    print(session.map_name, session.categorized_entities)