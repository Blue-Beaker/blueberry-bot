from nonebot import logger, require
from nonebot.dependencies import Dependent
from nonebot.internal.adapter import Bot,Event
from nonebot.matcher import Matcher
from nonebot.permission import Permission
from typing import Any, Type
from .utils import get_matcher_references,get_all_matchers

require("bbot_api")
from ..bbot_api.group_config.permgroup_manager import get_permgroup_manager
from ..bbot_api import getid


class CommandPermEntry:
    # Command ID
    cmd_id:str
    rule_chain:list[tuple[str,bool]]
    
    def __init__(self,cmd_id:str) -> None:
        self.cmd_id=cmd_id
        self.rule_chain=[]
    # Add rule at the end or the specified position
    def add_rule(self,group:str,enable:bool,index:int|None=None):
        if index is not None and index < self.rule_chain.__len__():
            self.rule_chain.insert(index,(group,enable))
        else:
            self.rule_chain.append((group,enable))
        return self
    def remove_rule(self,index:int|None=None):
        if not index or index>=self.rule_chain.__len__():
            index=-1
        self.rule_chain.pop(index)
        return self
    # Check whether the rule applies to the matcher
    def is_applicable(self,matcher:Type[Matcher]):
        refers = get_matcher_references(matcher)
        return self.cmd_id in refers
    # Check permission
    def check_permission(self,bot:Bot,event:Event):
        group_id = getid(event)
        permgroups = get_permgroup_manager().get_group_permgroups(group_id)
        
        reverse_chain=self.rule_chain.copy()
        reverse_chain.reverse()
        
        # logger.info(f"{self.rule_chain} {reverse_chain}")
        # logger.info(f"{group_id} {permgroups}")
        for group,enable in reverse_chain:
            # logger.info(f"{group} {enable}")
            if (group == group_id) or (group in permgroups) or (group == "global"):
                return enable
        return True
    
    def to_dict(self):
        data:dict[str,Any]={}
        data['command']=self.cmd_id
        data['rules']=[CommandPermEntry.format_rule(g,e) for g,e in self.rule_chain]
        return data
    @classmethod
    def from_dict(cls,data:dict[str,Any]):
        cmd = data.get('command',None)
        if not cmd:
            return None
        inst=cls(cmd)
        
        rules = data.get('rules',[])
        for r in rules:
            rule = CommandPermEntry.parse_rule(r)
            if rule:
                inst.rule_chain.append(rule)
                
        return inst
        
    @staticmethod
    def format_rule(group:str,enable:bool):
        return f"{group}={enable}"
    
    @staticmethod
    def parse_rule(rule:str):
        spl=[s.strip() for s in rule.split("=")]
        if spl.__len__()<2:
            return None
        if spl[1].lower() not in ['0','1','true','false','t','f']:
            return None
        return (spl[0],spl[1].lower() in ['1','true','t'])
        
class CommandPermManager:
    entries:dict[str,CommandPermEntry]={}
    def __init__(self) -> None:
        self.entries={}
    def add_entry(self,entry:CommandPermEntry):
        self.entries[entry.cmd_id]=entry
        
    def get_rule(self,entry_id:str):
        return self.entries.get(entry_id,None)
    
    def add_rule(self,entry_id:str,group:str,enable:bool,index:int|None=None):
        if entry_id not in self.entries:
            self.entries[entry_id]=CommandPermEntry(entry_id)
        self.entries[entry_id].add_rule(group,enable,index)
        return self
    
    def remove_rule(self,entry_id:str,index:int|None=None):
        if entry_id not in self.entries:
            return
        self.entries[entry_id].remove_rule(index)
        if self.entries[entry_id].rule_chain.__len__()==0:
            self.entries.pop(entry_id)
        return self
        
    def check_permission(self,matcher:Type[Matcher]|Matcher,bot:Bot,event:Event):
        refers = get_matcher_references(matcher)
        for r in refers:
            if r in self.entries.keys() and not self.entries[r].check_permission(bot,event):
                return False
        return True