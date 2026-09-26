from enum import Enum
import json
import os
from nonebot import logger, require
from nonebot.dependencies import Dependent
from nonebot.internal.adapter import Bot,Event
from nonebot.matcher import Matcher
from nonebot.permission import Permission
from typing import Any, Type
from .utils import format_matcher_references,get_matcher_references,get_all_matchers,MatcherReference

require("bbot_api")
from ..bbot_api.group_config.permgroup_manager import get_permgroup_manager
from ..bbot_api import getid

class CommandMatcher(MatcherReference):
    def is_applicable(self,matcher:MatcherReference|Type[Matcher]|Matcher):
        if isinstance(matcher,MatcherReference):
            if not(self.plugin_id=="*" or self.plugin_id==matcher.plugin_id):
                return False
            return self.command=="*" or self.command==matcher.command
        
        refers = get_matcher_references(matcher)
        return any([self.is_applicable(r) for r in refers])

class PermAction(Enum):
    ALLOW=1
    DENY=2
    IGNORE=3

class CommandPermEntry:
    group:str="*"
    commands:list[CommandMatcher]
    action:PermAction=PermAction.ALLOW
    priority:int=0
    
    def __init__(self) -> None:
        self.commands=[]
        pass
    # Check whether the rule applies to the matcher
    def check_command(self,matcher:MatcherReference|Type[Matcher]|Matcher):
        for c in self.commands:
            if c.is_applicable(matcher):
                return True
        return False
    # Check permission
    def check_group(self,bot:Bot,event:Event):
        group_id = getid(event)
        permgroups = get_permgroup_manager().get_group_permgroups(group_id)
        
        group=self.group
        if (group == group_id) or (group in permgroups) or (group == "*"):
            return True
        return False
    def get_action(self):
        return self.action
    
    def get_sort_key(self):
        return (self.priority,self.group,','.join([c.__str__() for c in self.commands]))
    
    def to_dict(self):
        data:dict[str,Any]={}
        data['group']=self.group
        data['commands']=[c.__str__() for c in self.commands]
        data['action']=self.action.value
        data['priority']=self.priority
        return data
    @classmethod
    def from_dict(cls,data:dict[str,Any]):
        inst=cls()
        inst.group=str(data.get('group','*'))
        commands = list(data.get('commands',[]))
        for c in commands:
            inst.commands.append(CommandMatcher.from_str(c))
        inst.action=PermAction(int(data.get('action',1)))
        inst.priority=int(data.get('priority',0))
        return inst
    
    # <group> <commands> <action> [priority]
    def dump_rule(self):
        return f"{self.group} {','.join([c.__str__() for c in self.commands])} {self.action.name} {self.priority}"
    
    @classmethod
    def build(cls,group:str,commands:list[CommandMatcher],action:PermAction,priority:int=0):
        inst=cls()
        inst.group=group
        inst.commands=commands.copy()
        inst.action=action
        inst.priority=priority
        return inst
    
    @classmethod
    def load_rule(cls,rule:str):
        spl=[s.strip() for s in rule.split()]
        if spl.__len__()<3:
            return None
        group=spl[0]
        
        commands = [CommandMatcher.from_str(cmd.strip()) for cmd in spl[1].split(',')]
        
        action=PermAction.__members__.get(spl[2].upper(),None)
        if not action:
            raise ValueError(f"Value error: {spl[2].upper()}, valid are {','.join(PermAction.__members__)}")
        
        priority=int(spl[3]) if spl.__len__()>=4 else 0
        
        return cls.build(group,commands,action,priority)
        
class CommandPermManager:
    entries:list[CommandPermEntry]=[]
    config_path:str|None=None
    def __init__(self,config_path:str|None=None) -> None:
        self.entries=[]
        self.config_path=config_path
        
    def add_entry(self,entry:CommandPermEntry):
        self.entries.append(entry)
        self.sort()
    def sort(self):
        self.entries.sort(key=CommandPermEntry.get_sort_key,reverse=True)
    
    def add_rule(self,group:str,commands:list[CommandMatcher],action:PermAction,priority:int=0):
        self.add_entry(CommandPermEntry.build(group,commands,action,priority))
        return self
    
    def remove_rule(self,index:int|None=None):
        if index==None:
            index=-1
        return self.entries.pop(index)
    
    def get_command_rules(self,matcher:MatcherReference|Type[Matcher]|Matcher):
        result:list[CommandPermEntry]=[]
        for e in self.entries:
            if e.check_command(matcher):
                result.append(e)
        return result
        
    def check_permission(self,matcher:Type[Matcher]|Matcher,bot:Bot,event:Event):
        for e in self.entries:
            if not e.check_group(bot,event):
                continue
            if not e.check_command(matcher):
                continue
            return e.action
        return PermAction.ALLOW
    
    def to_dict(self):
        data:dict[str,Any]={}
        data["entries"]=[e.dump_rule() for e in self.entries]
        return data
    
    def load_dict(self,data:dict[str,Any]):
        if not isinstance(data,dict):
            logger.error(f"Failed to load command perms: {data}")
            return
        entries:list[CommandPermEntry]=[]
        for line in list(data.get("entries",[])):
            entry=CommandPermEntry.load_rule(line)
            if not entry:
                continue
            entries.append(entry)
            
        self.entries.clear()
        for e in entries:
            self.add_entry(e)
        return self
    
    def save(self):
        if not self.config_path:
            return False
        os.makedirs(os.path.dirname(self.config_path),exist_ok=True)
        with open(self.config_path,"w") as f:
            json.dump(self.to_dict(),f)
            
    def load(self):
        if not self.config_path:
            return False
        if not os.path.isfile(self.config_path):
            return False
        with open(self.config_path,"r") as f:
            self.load_dict(json.load(f))