from enum import Enum
from typing import Any, Callable, Awaitable, Iterable, Sequence, TypeVar
from nonebot import logger
from nonebot.adapters import Bot,Event
from .models import Priority,HELP_FUNC_TYPE,HELP_RETURN_TYPE
from .impl import HelpRegistry
    
HELP_REGISTRY=HelpRegistry()
SUPERUSER_HELP_REGISTRY=HelpRegistry()

def addHelpFunc2(priority:int|Priority=Priority.NORMAL):
    return HELP_REGISTRY.addHelpFunc2(priority)
def addHelpFunc(func:HELP_FUNC_TYPE):
    return HELP_REGISTRY.addHelpFunc(func)

async def getAllHelp(bot:Bot,event:Event):
    return await HELP_REGISTRY.getAllHelp(bot,event)