
import asyncio
import math
import re
import threading
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

def split_str_lists(text:str) -> list[str]:
    return [i.strip() for i in text.split(",")] if text.strip() else []


def has_skills(search:list[str],level_skills:list[str],skill_groups:list[list[str]]=[]):
    lskills=set()
    for s in level_skills:
        lskills.add(s.lower())
        if " " in s:
            lskills.add(s.lower().replace(" ",""))
    
    for group in skill_groups:
        intersect=list(set(group) & set(lskills))
        if intersect:
            lskills=list(set(group) | set(lskills))
    matched=True
    for s in search:
        if s.lower() not in lskills:
            matched=False
            break
    return matched

class SearchException(Exception):
    def __init__(self, msg:str, *args: object) -> None:
        super().__init__(*args)
        self.msg=msg
    def __str__(self) -> str:
        return self.get_message()+super().__str__()
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

def searchInName(search:str,name:str,fuzzy:bool):
    if fuzzy:
        return search.lower() in name.lower()
    else:
        patt = re.compile(r"(.*)\(.*\)")
        matched=patt.match(name)
        if matched:
            name=matched.group(1)
        return search.lower().strip() == name.lower().strip()
    

_A = TypeVar(name="_A")
def safeInt(i:Any,fallback:_A=-1) -> int|_A:
    return safeConversion(i,int,-1)
    
def safeFloat(i:Any,fallback:_A=-1.0) -> float|_A:
    return safeConversion(i,float,-1.0)
    
_T = TypeVar(name="_T")
def safeConversion(i:Any, converter:Callable[[Any],_T],fallback:_A=None) -> _T|_A:
    try:
        return converter(i)
    except:
        return fallback
    
async def async_run_thread(thread:threading.Thread, check_interval:float=0.1):
    thread.start()
    while thread.is_alive():
        await asyncio.sleep(check_interval)
    