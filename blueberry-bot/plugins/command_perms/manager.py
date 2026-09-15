from nonebot import logger, require
from nonebot.dependencies import Dependent
from nonebot.internal.adapter import Bot,Event
from nonebot.matcher import Matcher
from nonebot.permission import Permission
from typing import Type
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
        
class CommandPermManager:
    entries:dict[str,CommandPermEntry]={}
    def __init__(self) -> None:
        self.entries={}
    def add_entry(self,entry:CommandPermEntry):
        self.entries[entry.cmd_id]=entry
    def check_permission(self,matcher:Type[Matcher]|Matcher,bot:Bot,event:Event):
        refers = get_matcher_references(matcher)
        for r in refers:
            if r in self.entries.keys() and not self.entries[r].check_permission(bot,event):
                return False
        return True