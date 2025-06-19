

import json
import os
import re
import sys
import traceback
from typing import Any

sys.path.append(".")

from utils.constants import *

# 用于预处理地图数据时给实体归类
attribute_rule_matcher=re.compile("(.+)([<>]=?|==|!=)(.+)")

def getName(child:dict):
    if not isinstance(child,dict):
        print(child)
    if("name" in child.keys()):
        return str(child["name"])
    return "null"

def getAttributes(obj:dict):
    if("attributes" in obj.keys()):
        return obj["attributes"]
    return {}

#可选规则, 筛选特定条件的实体
class AttributeMatchingRule:
    rulestr:str
    def __init__(self,rulestr:str) -> None:
        self.rulestr=rulestr
    def matches(self,entity_attributes:dict[str,Any])->bool:
        for k,v in entity_attributes.items():
            locals()[k]=v
        try:
            return eval(self.rulestr)
        except Exception as e:
            print(f"Trying to eval {self.rulestr} with {entity_attributes}:")
            print(locals())
            traceback.print_exc()
            raise e
            return False

# 预处理时使用的实体标签类 经过简化
class EntityCategoryPre:
    id:str
    name:str
    entities:list[str]
    entity_with_attr_rule:dict[str,str]
    
    def __init__(self,name:str,entities:list[str]) -> None:
        self.name=name
        self.entities=[]
        self.entity_with_attr_rule={}
        for e in entities:
            if("#" in e):
                spl=e.split("#",1)
                self.entity_with_attr_rule[spl[0]]=spl[1]
            else:
                self.entities.append(e)
        
    @classmethod
    def from_json(cls,json_data:dict):
        inst=EntityCategoryPre(json_data["name"],json_data["entities"])
        return inst
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.id} {self.name}"
    def info(self) -> str:
        return f"{self.__class__.__name__}, entities=[{', '.join(self.entities)}]"
    def countEntities(self,entities:list[dict]):
        count=0
        for entity in entities:
            if(self.doesEntityMatch(entity)):
                count=count+1
    def doesEntityMatch(self,entity:dict):
        name=getName(entity)
        if(name in self.entities):
            return True
        # 如果实体有额外条件, 判断它们
        # 实体条件为一个返回bool类型的python表达式
        if(name in self.entity_with_attr_rule):
            attrRule=self.entity_with_attr_rule[name]
            attrs=getAttributes(entity)
            rule=AttributeMatchingRule(attrRule)
            return rule.matches(attrs)
        return False    
        # process entity with attributes
        

class EntityDataManagerPre:
    category_data:dict[str,EntityCategoryPre]
    entity_to_categories:dict[str,list[EntityCategoryPre]]
    
    def load(self):
        self.category_data={}
        self.entity_to_categories={}
        # 读取实体类别文件
        with open(ENTITY_CATEGORIES_FILE) as f:
            data:dict[str,dict]=json.load(f)
        for k,v in data.items():
            # load category from json
            try:
                self.category_data[k]=EntityCategoryPre.from_json(v)
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
                
            for e in cat.entity_with_attr_rule:
                e=e.split("#",1)[0]
                # if the list isn't there, create it
                if e not in self.entity_to_categories.keys():
                    self.entity_to_categories[e]=[]
                self.entity_to_categories[e].append(cat)
                
    def get_categories(self,entity:str)->list[EntityCategoryPre]:
        if(entity in self.entity_to_categories.keys()):
            return self.entity_to_categories[entity].copy()
        return []
    