from enum import Enum
import os,json
import traceback

DATA_DIR="blueberry-bot/plugins/guess/data"

class CountMode(Enum):
    BOOLEAN=0
    RANGE=1
    PRECISE=2
    @classmethod
    def from_name(cls,name:str):
        return cls.__dict__[name.upper()]
class MentionMode(Enum):
    PRESENT=0
    NOT_PRESENT=1
    ALWAYS=2
    @classmethod
    def from_name(cls,name:str):
        return cls.__dict__[name.upper()]

class EntityCategory:
    id:str
    name:str
    count_mode:CountMode
    mention_when:MentionMode
    entities:list[str]
    def __init__(self,name:str,entities:list[str],count_mode:str="range",mention_when:str="present") -> None:
        self.name=name
        self.entities=entities
        # Where to count the entity or simply says it's in the map.
        self.count_mode=CountMode.from_name(count_mode)
        # Whether to mention the entity even when it's not in the map.
        self.mention_when=MentionMode.from_name(mention_when)
        
    @classmethod
    def from_json(cls,json_data:dict):
        inst=EntityCategory(json_data["name"],json_data["entities"])
        if("count_mode" in json_data.keys()):
            inst.count_mode=CountMode.from_name(json_data["count_mode"])
        if("mention_when" in json_data.keys()):
            inst.mention_when=MentionMode.from_name(json_data["mention_when"])
        return inst
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.id} {self.name}"
    def info(self) -> str:
        return f"{self.__class__.__name__}, count_mode={self.count_mode}, mention_when={self.mention_when}, entities=[{', '.join(self.entities)}]"

class EntityDataManager:
    category_data:dict[str,EntityCategory]
    entity_to_categories:dict[str,list[EntityCategory]]
    def load(self):
        self.category_data={}
        self.entity_to_categories={}
        with open(os.path.join(DATA_DIR,"entity_categories.json")) as f:
            data:dict[str,dict]=json.load(f)
        for k,v in data.items():
            # load category from json
            try:
                self.category_data[k]=EntityCategory.from_json(v)
                self.category_data[k].id=k
            except Exception as e:
                print("Error when reading: ",k,v)
                raise e
            
    def process(self):
        for id,cat in self.category_data.items():
            # add to entity_to_categories
            for e in cat.entities:
                # if the list isn't there, create it
                if e not in self.entity_to_categories.keys():
                    self.entity_to_categories[e]=[]
                self.entity_to_categories[e].append(cat)
    def get_categories(self,entity:str)->list[EntityCategory]:
        if(entity in self.entity_to_categories.keys()):
            return self.entity_to_categories[entity].copy()
        return []
    
    
class MapData:
    filePath:str
    name:str
    aliases:list[str]
    id:str
    def __init__(self,name:str,filePath:str,aliases:list[str]=[]) -> None:
        self.name=name
        self.aliases=aliases
        self.filePath=filePath
        
    @classmethod
    def from_json(cls,json_data:dict):
        inst=MapData(json_data["name"],json_data["filePath"])
        if("aliases" in json_data.keys()):
            inst.aliases=json_data["aliases"].copy()
        return inst
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.id} {self.name}"
    def info(self) -> str:
        return f"{self.__class__.__name__}, filePath={self.filePath}, aliases=[{', '.join(self.aliases)}]"


class MapDataManager:
    map_data:dict[str,MapData]
    file_to_mapdata:dict[str,MapData]
    alias_to_mapdata:dict[str,MapData]
    def load(self):
        self.map_data={}
        self.alias_to_mapdata={}
        with open(os.path.join(DATA_DIR,"map_data.json")) as f:
            data:dict[str,dict]=json.load(f)
        for k,v in data.items():
            # load category from json
            try:
                self.map_data[k]=MapData.from_json(v)
                self.map_data[k].id=k
            except Exception as e:
                print("Error when reading: ",k,v)
                raise e
            
    def process(self):
        for id,mapData in self.map_data.items():
            # add to entity_to_categories
            for e in mapData.aliases:
                self.alias_to_mapdata[e]=mapData
            self.file_to_mapdata[mapData.filePath]=mapData
    def get_map_from_alias(self,map:str):
        return self.alias_to_mapdata[map] if map in self.alias_to_mapdata.keys() else None
    def get_map_from_file(self,map:str):
        return self.file_to_mapdata[map] if map in self.file_to_mapdata.keys() else None

ENTITY_MANAGER=EntityDataManager()
MAP_MANAGER=MapDataManager()

def load_all_data():
    ENTITY_MANAGER.load()
    ENTITY_MANAGER.process()
    MAP_MANAGER.load()
    MAP_MANAGER.process()

if __name__ == '__main__':
    manager=EntityDataManager()
    manager.load()
    manager.process()
    print(manager,manager.category_data)