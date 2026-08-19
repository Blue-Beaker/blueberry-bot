from enum import Enum
import traceback
from typing import Any, Callable, Awaitable, Iterable, Sequence, TypeVar
from nonebot import logger
from nonebot.adapters import Bot,Event
import inspect

HELP_RETURN_TYPE=str|Iterable[str]|None

HELP_FUNC_TYPE=Callable["...",HELP_RETURN_TYPE|Awaitable[HELP_RETURN_TYPE]]
_H = TypeVar('_H',bound=HELP_FUNC_TYPE)

class Priority(Enum):
    VERY_EARLY=-1000
    EARLY=-100
    NORMAL=0
    LATE=100
    VERY_LATE=1000

class HelpEntry:
    func:HELP_FUNC_TYPE
    priority:int
    def __init__(self,func:HELP_FUNC_TYPE,priority:int|Priority=Priority.NORMAL) -> None:
        self.func=func
        self.priority=priority if isinstance(priority,int) else priority.value
    def __lt__(self,other:"HelpEntry"):
        return self.priority<other.priority
    def __gt__(self,other:"HelpEntry"):
        return self.priority>other.priority

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
    
HELP_REGISTRY=HelpRegistry()

def addHelpFunc2(priority:int|Priority=Priority.NORMAL):
    return HELP_REGISTRY.addHelpFunc2(priority)
def addHelpFunc(func:HELP_FUNC_TYPE):
    return HELP_REGISTRY.addHelpFunc(func)

async def getAllHelp(bot:Bot,event:Event):
    return await HELP_REGISTRY.getAllHelp(bot,event)