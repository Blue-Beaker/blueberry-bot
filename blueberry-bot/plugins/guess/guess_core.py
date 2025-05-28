import json
import math
import random
import os,sys
from nonebot import logger

sys.path.append(".")

from . import utils,guess_data
from .guess_data import EntityCategory,MapData,ENTITY_MANAGER,MAP_MANAGER

from constants import *

def getMapJsonFromPath(path:str):
    mapPath=os.path.join(MAP_DATA_DIR,path)
    with open(mapPath) as f:
        return json.load(f)

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
    guesses_per_info:int=3
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
        logger.debug(f"{self.map_name}:\n{self.entities_to_pick}\n{self.entities}")
    
    
    def entityCount(self,entity:str)->int:
        return self.entities[entity] if entity in self.entities else 0
    
    def count_categories(self):
        self.categorized_entities:dict[EntityCategory,int]={}
        self.entities_to_pick:dict[EntityCategory,int]={}
        taggedEntities:dict[str,int]=self.map_jsondata['entityTagCount']
        
        for tagID,count in taggedEntities.items():
            category = ENTITY_MANAGER.category_data.get(tagID)
            if(category):
                self.categorized_entities[category]=count
                if(category.matchesCount(count)):
                    self.entities_to_pick[category]=count
        
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
                self.entities_to_pick[cat]=0
    
    def unrevealed_entities(self):
        choices:list[tuple[EntityCategory,int]]=[]
        for c in self.entities_to_pick.items():
            if c[0] not in self.revealed_info.keys():
                choices.append(c)
        return choices
    
    def get_info(self)->tuple[EntityCategory,int]:
        unrevealed=self.unrevealed_entities()
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
    
    @property
    def guesses_for_next_info(self):
        return self.revealed_info.__len__()*self.guesses_per_info
    
    def on_guess_wrong(self)->str:
        if(self.unrevealed_entities().__len__()>0):
            if (self.guesses>=self.guesses_for_next_info):
                self.reveal_info()
            else:
                return f"回答错误! 再猜{self.guesses_for_next_info-self.guesses}次加一条线索 题目是: "
        return f"回答错误! 题目是: "
        
    def do_guess(self,msg:str)->str:
        
        self.guesses=self.guesses+1
        
        msg=msg.strip()
        logger.info(msg)
        map=MAP_MANAGER.get_map_from_alias(msg)
        feedback=[]
        
        if(map==self.map_name or msg in self.aliases):
            self.finished=True
            feedback.append(f"你猜对了! 正确答案是: {self.map_name}, 本题共猜了{self.guesses}次")
        else:
            if(not map):
                feedback.append("没有找到你输入的地图! 请输入正确的地图名或别称")
            else:
                feedback.append(self.on_guess_wrong())
            feedback.append(self.get_final_message())
            
        feedback[0]="{username} "+feedback[0]
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
        
            
        self.session=GuessSession(map,getMapJsonFromPath(map.filePath))
        return self.session
    
    def start(self)->str:
        if(self.session):
            return "当前有正在进行的guess 请先猜出来或放弃\n"+self.session.get_final_message()
        self.session=self._start_guess()
        self.session.reveal_info()
        return "你能根据以下信息猜出这是哪张图吗? 输入&guess 你的答案 以回答\n"+self.session.get_final_message()
    
    def cancel(self)->str:
        if(not self.session):
            return "当前没有正在进行的guess"
        session=self.session
        self.session=None
        return f"{{username}} 猜了{session.guesses}次后, 你放弃了! 答案是: {session.map_name}"
    
    def do_guess(self,msg:str) -> str:
        if(not self.session):
            return "当前没有正在进行的guess 请&guess start开始猜图"
        result=self.session.do_guess(msg)
        if(self.session.finished):
            self.session=None
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
            dumpdata["guesses_per_info"]=self.session.guesses_per_info
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
            
            jsondata=getMapJsonFromPath(mapData.filePath)
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
                
            guesses_per_info=dumpdata.get("guesses_per_info",None)
            if(isinstance(guesses_per_info,int)):
                session.guesses_per_info=guesses_per_info
                
        return inst