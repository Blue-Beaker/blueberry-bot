from nonebot import require,get_loaded_plugins
from nonebot.matcher import Matcher
from nonebot.plugin import Plugin
from typing import Type
from nonebot.permission import SUPERUSER,Permission
from nonebot.rule import CommandRule

class MatcherReference:
    plugin_id:str|None=None
    command:str=""
    def __init__(self,plugin_id:str|None,command:str) -> None:
        self.plugin_id=plugin_id
        self.command=command
    def format(self) -> str:
        return f"{self.plugin_id}:{self.command}"
    def __str__(self) -> str:
        return self.format()
    @classmethod
    def from_str(cls,line:str):
        spl=line.split(":",2)
        return cls(spl[0],spl[1])

def get_matcher_references(matcher:Type[Matcher]|Matcher) -> list[MatcherReference]:
    dependent=None
    command=None
    plugin_id=matcher.plugin_id or "_unknown"
    for c in matcher.rule.checkers:
        call = c.call
        if isinstance(call,CommandRule):
            dependent=c
            command=call
        break
    if not dependent or not command:
        return []
    return [MatcherReference(plugin_id,cmd[0]) for cmd in command.cmds]

def format_matcher_references(matcher:Type[Matcher]|Matcher) -> list[str]:
    return [ref.format() for ref in get_matcher_references(matcher)]

def is_permission_manageable(matcher:Type[Matcher]|Matcher):
    if matcher.permission==SUPERUSER:
        return False
    return True

def get_all_matchers(plugin_name:str|None=None):
    matchers:dict[str,Type[Matcher]]={}
    for plugin in get_loaded_plugins():
        if plugin_name and plugin_name!=plugin.id_:
            continue
        for matcher in plugin.matcher:
            if not is_permission_manageable(matcher):
                continue
            refers = format_matcher_references(matcher)
            for r in refers:
                matchers[r]=matcher
    return matchers