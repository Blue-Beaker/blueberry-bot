from .models import HELP_FUNC_TYPE,HELP_RETURN_TYPE,Priority,HelpEntry
from collections.abc import Awaitable
from enum import Enum
from typing import Any, Callable, Iterable, TypeVar
from nonebot import logger
import inspect
import traceback
from nonebot.adapters import Bot,Event

_H = TypeVar('_H',bound=HELP_FUNC_TYPE)

class HelpRegistry:
    help_funcs:list[HelpEntry]=[]
    
    def __init__(self) -> None:
        self.help_funcs=[]
    
    def addHelpFunc2(self,priority:int|Priority=Priority.NORMAL):
        def wrapper(func:_H) -> _H:
            self.help_funcs.append(HelpEntry(func,priority))
            return func
        return wrapper
    
    def addHelpFunc(self,func:_H) -> _H:
        self.help_funcs.append(HelpEntry(func))
        return func
    
    async def getAllHelp(self,bot:Bot,event:Event):
        lines:list[str] = []
        for entry in sorted(self.help_funcs):
            func=entry.func
            signature=inspect.signature(func)
            params = signature.parameters.values()
            
            has_bot_arg:bool=False
            has_event_arg:bool=False
            
            kwargs:dict[str,Any]={}
            
            skip=False
            
            for param in params:
                name=param.name
                type1=param.annotation
                default=param.default
                
                # logger.info(type1)
                if not has_bot_arg and issubclass(type1,Bot):
                    if not isinstance(bot,type1):
                        skip=True
                        break
                    has_bot_arg=True
                    kwargs[name]=bot
                    
                if not has_event_arg and issubclass(type1,Event):
                    if not isinstance(event,type1):
                        skip=True
                        break
                    has_event_arg=True
                    kwargs[name]=event
            if skip:
                continue
            try:
                result = func(**kwargs)
                if isinstance(result,Awaitable):
                    result = await result
                    
                if isinstance(result,str):
                    lines.append(result)
                elif isinstance(result,Iterable):
                    lines.extend(result)
            except Exception as e:
                logger.error(f"Error fetching help for {func} in {func.__module__}: {e}")
                logger.debug(traceback.format_exc())
                
        return lines