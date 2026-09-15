from nonebot import require,get_loaded_plugins
from nonebot.matcher import Matcher
from typing import Type
from nonebot.permission import SUPERUSER,Permission
from nonebot.rule import CommandRule

def get_matcher_references(matcher:Type[Matcher]|Matcher):
    dependent=None
    command=None
    for c in matcher.rule.checkers:
        call = c.call
        if isinstance(call,CommandRule):
            dependent=c
            command=call
        break
    if not dependent or not command:
        return []
    return [(matcher.plugin_id+':'+cmd[0] if matcher.plugin_id else cmd[0]) for cmd in command.cmds]

def is_permission_manageable(matcher:Type[Matcher]|Matcher):
    if matcher.permission==SUPERUSER:
        return False
    return True

def get_all_matchers():
    matchers:dict[str,Type[Matcher]]={}
    for plugin in get_loaded_plugins():
        for matcher in plugin.matcher:
            if matcher.permission==SUPERUSER:
                continue
            refers = get_matcher_references(matcher)
            for r in refers:
                matchers[r]=matcher
    return matchers