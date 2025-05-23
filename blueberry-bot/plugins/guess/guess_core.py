import json
import random
import os,sys
from . import utils,guess_data
from .guess_data import EntityCategory,MapData,MAP_DATA_DIR,DATA_DIR,ENTITY_MANAGER,MAP_MANAGER

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
    revealed_info:dict[EntityCategory,int]
    entities:dict[str,int]
    
    def __init__(self,mapData:MapData,map_exported_data:dict) -> None:
        self.mapData=mapData
        
        self.guesses=0
        self.revealed_info={}
        self.finished=False
        
        self.map_jsondata=map_exported_data
        self.entities=map_exported_data['entities']
        self.count_categories()
        print(f"{self.map_name}:\n{self.categorized_entities}\n{self.entities}")
    
    
    def entityCount(self,entity:str)->int:
        return self.entities[entity] if entity in self.entities else 0
    def count_categories(self):
        self.categorized_entities:dict[EntityCategory,int]={}
        taggedEntities:dict[str,int]=self.map_jsondata['entityTagCount']
        for tagID,count in taggedEntities.items():
            category = ENTITY_MANAGER.category_data.get(tagID)
            if(category):
                self.categorized_entities[category]=count
                
        # # 根据实体增加对应类别计数
        # for entity in self.entities:
        #     for category in ENTITY_MANAGER.get_categories(entity):
        #         if(category not in self.categorized_entities.keys()):
        #             self.categorized_entities[category]=self.entityCount(entity)
        #         else:
        #             self.categorized_entities[category]=self.categorized_entities[category]+self.entityCount(entity)
        # 增加不存在的实体
        for cat in ENTITY_MANAGER.get_categories_not_present():
            if cat not in self.categorized_entities:
                self.categorized_entities[cat]=0
    
    def get_unrevealed_entity(self):
        choices:list[tuple[EntityCategory,int]]=[]
        for c in self.categorized_entities.items():
            if c[0] not in self.revealed_info.keys():
                choices.append(c)
        return choices
    
    def get_info(self)->tuple[EntityCategory,int]:
        unrevealed=self.get_unrevealed_entity()
        if(unrevealed.__len__()==0):
            self.finished=True
        choice=random.choice(unrevealed)
        return (choice[0],choice[1])
    
    def reveal_info(self):
        k,v=self.get_info()
        self.revealed_info[k]=v
    
    def get_message_from_revealed_info(self,k:EntityCategory,v:int)->str:
        if v==0:
            return f"没有{k.name}"
        return f"有{v}个{k.name}"
    
    def get_final_message(self):
        messageLines=[]
        for k,v in self.revealed_info.items():
            messageLines.append(self.get_message_from_revealed_info(k,v))
        return "\n".join(messageLines)
    
    def do_guess(self,msg:str)->str:
        msg=msg.strip()
        print(msg)
        map=MAP_MANAGER.get_map_from_alias(msg)
        feedback=[]
        
        if(not map):
            feedback.append("没有找到你输入的地图! 请输入正确的地图名或别称")
            
        if(map==self.map_name or msg in self.aliases):
            self.finished=True
            feedback.append(f"你猜对了! 正确答案是: {self.map_name}")
        else:
            if(self.get_unrevealed_entity().__len__()>0):
                self.reveal_info()
            feedback.append("回答错误! 题目是: ")
            feedback.append(self.get_final_message())
        return "\n".join(feedback)

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
        
        map=MAP_MANAGER.pickMap()
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
        return "你能根据以下信息猜出这是哪张图吗?\n"+self.session.get_final_message()
    
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
        print(self.dump())
        return result
    
    def dump(self):
        dumpdata={
        }
        revealed={}
        if(self.session):
            dumpdata["current_map"]=self.session.mapData.id
            for key,value in self.session.revealed_info.items():
                revealed[key.id]=value
            dumpdata["revealed_info"]=revealed
            dumpdata["guesses"]=self.session.guesses
        else:
            dumpdata["current_map"]=None
            
        return dumpdata

    @classmethod
    def load(cls,dumpdata:dict[str,str|list[str]|int]):
        inst=cls()
        map=dumpdata.get("current_map",None)
        if not isinstance(map,str):
            return inst
        mapData=MAP_MANAGER.get_map_from_id(map)
        if mapData:
            with open(mapData.filePath,"r") as f:
                jsondata=json.load(f)
            session=GuessSession(mapData,jsondata)
            inst.session=session
            
            info=dumpdata.get("revealed_info",None)
            if isinstance(info,dict):
                for id,value in info.items():
                    entity=ENTITY_MANAGER.category_data.get(id,None)
                    if not entity:
                        continue
                    session.revealed_info[entity]=value
                    
            guesses=dumpdata.get("guesses",None)
            if(isinstance(guesses,int)):
                session.guesses=guesses
                
        return inst
            
        
    
if __name__ == '__main__':
    manager=GuessManager()
    session=manager._start_guess()
    print(session.map_name, session.categorized_entities)