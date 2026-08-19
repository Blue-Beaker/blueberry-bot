
from collections.abc import Awaitable
from enum import Enum
from typing import Callable, Iterable, TypeVar


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