
import math
from typing import Any, Callable, TypeVar
from nonebot import require
from nonebot.matcher import Matcher

require("gd_api")
from ..gd_api.gd import getLevel2,Level,PageInfo,LevelList


T = TypeVar("T", bound=Any)
def select_page(results:list[T],count:int,entries_per_page:int,page:int):
    maxpages=1+((count-1)//entries_per_page)
    page=max(1,min(page,maxpages))
    if count>entries_per_page:
        results=results[(page-1)*entries_per_page:min(page*entries_per_page,count)]
    return results,maxpages,page

def repr_level(l:Level,fromuser:bool=False):
    return f"{l.name} by {l.creator} ({l.repr_difficulty()}) ({l.id})" if not fromuser else f"{l.name} ({l.repr_difficulty()}) ({l.id})"

def repr_list(l:LevelList,fromuser:bool=False):
    return f"{l.name} by {l.creator} ({l.id}) ({l.levels.__len__()} 个关卡)" if not fromuser else f"{l.name} ({l.id}) ({l.levels.__len__()} 个关卡)"



class SearchException(Exception):
    def __init__(self, msg:str, *args: object) -> None:
        super().__init__(*args)
        self.msg=msg
    def get_message(self):
        return self.msg
    
REPR_LEVEL_FUNC:Callable[[Level],str]=repr_level

# Ensures exactly one GD level for later use.
# When not exactly one level, a SearchException is raised, with the message to reply to the user.
def ensure_gd_level(levels:list[Level]|None,pageinfo:PageInfo,repr_level_function:Callable[[Level],str]|None=None) -> Level:
    if not repr_level_function:
        repr_level_function=REPR_LEVEL_FUNC
    if not isinstance(levels,list) or not pageinfo.success():
        raise SearchException("查找出错."+pageinfo.status.value)
    if levels.__len__()==0:
        raise SearchException("没有查找到任何关卡.")
    elif levels.__len__()>1:
        lines=[]
        lines.append("找到多个关卡,请用id选择:")
        lines.append(f"第 {pageinfo.offset/pageinfo.amount}/{math.ceil(pageinfo.total/pageinfo.amount)} 页 ({pageinfo.offset}-{pageinfo.offset+pageinfo.amount}/{pageinfo.total})")
        for l in levels:
            lines.append(repr_level_function(l))
        raise SearchException("\n".join(lines))
    return levels[0]