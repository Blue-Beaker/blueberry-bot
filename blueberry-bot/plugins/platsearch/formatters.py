from typing import Any, Callable,TypeVar
from .plat_sheets import PlatChartEntry,NLWLikeEntry,LevelEntry

from .models.gdapi import AREDLLevel,PemonlistLevel

_FORMAT_FUNCS:dict[type,Callable[[Any,bool,bool],str]]={
}

def format(l:PlatChartEntry|AREDLLevel|PemonlistLevel|NLWLikeEntry,compact:bool=False,exclude_base_info:bool=False):
    for k,v in _FORMAT_FUNCS.items():
        if isinstance(l,k):
            return v(l,compact,exclude_base_info)
    return f"Error type {type(l)}"

def set_formatters():
    _set_formatter(PlatChartEntry,formatDiffChart)
    _set_formatter(NLWLikeEntry,formatListsLevel)
    _set_formatter(PemonlistLevel,formatPemonlist)
    _set_formatter(AREDLLevel,formatAREDLLevel)

_T=TypeVar("_T")
def _set_formatter(t:type[_T],f:Callable[[_T,bool,bool],str]):
    _FORMAT_FUNCS[t]=f
    return f

def formatDiffChart(l:PlatChartEntry,compact:bool=False,exclude_base_info:bool=False):
    lines:list[str]=[]
    l1=""
    if not exclude_base_info:
        l1+=l.name
        if l.id>=0:
            l1+=(f" ({l.id})")
    if l.tier:
        if exclude_base_info:
            l1+=f"Tier {l.tier}"
        else:
            l1+=(f"(T{l.tier})")
    
    lines.append(l1)
    if not compact:
        if l.tags:
            lines.append(f"Tags: {','.join(l.tags)}")
            
        rankline=[]
        if l.enj and l.enj!="/":
            rankline.append(f"Enj: {l.enj}")
        if l.tpl and l.weight and l.tpl==l.weight:
            rankline.append(f"TPL/Weight: {l.tpl}")
        else:
            if l.tpl:
                rankline.append(f"TPL: {l.tpl}")
            if l.weight:
                rankline.append(f"Weight: {l.weight}")
        if l.pemon:
            rankline.append(f"Pemonlist: {l.pemon}")
            
        if rankline:
            lines.append(",".join(rankline))
    else:
        tagstr=','.join(l.tags) if l.tags else ""
        if tagstr.__len__()>15:
            tagstr=tagstr[0:13]+"..."
        lines.append(f"E{l.enj or '-'},W{l.weight or l.tpl or '-'},P{l.pemon or '-'}")
        lines.append(f" {tagstr}")
        return "".join(lines)
    
    return "\n".join(lines)

def formatListsLevel(l:NLWLikeEntry,compact:bool=False,exclude_base_info:bool=False,description:bool=True):
    lines:list[str]=[]
    
    if not exclude_base_info:
        firstline=f"{l.name} by {l.creator} ({l.sheet} {l.get_section()})"
    else:
        firstline=f"{l.sheet} {l.get_section()}"
        
    if not compact:
        lines.append(firstline)
        if not exclude_base_info and l.id:
            lines.append(f"ID ({l.id})")
        lines.append(f"Checkpoints: {l.checkpoints}, Skillsets: {",".join(l.skillsets)}")
        if description:
            lines.append(f"Description: {l.description}")
    else:
        line=firstline
        if l.checkpoints:
            line+=f" ◆{l.checkpoints}"
        lines.append(line)
    return "\n".join(lines)

def formatAREDLLevel(l:AREDLLevel,compact:bool=False,exclude_base_info:bool=False,description:bool=True):
    lines:list[str]=[]
    if not exclude_base_info:
        lines.append(f"{l.name} ({l.level_id}) AREDL #{l.position} Points: {l.points}")
    else:
        line=f"#{l.position} Points: {l.points}"
        if l.name.__contains__("(2P)"):
            line="2P "+line
        lines.append(line)
        
    if not compact:
        lines.append(f"Tags: {", ".join(l.tags)}")
        if l.edel_enjoyment >= 0:
            lines.append(f"EDEL Enj: {l.edel_enjoyment:.2f}{'(P)' if l.is_edel_pending else ''}")
        if l.gddl_tier>0:
            lines.append(f"GDDL Tier: {l.gddl_tier:.2f}")
        if description:
            lines.append(f"Description: {l.description}")
        
    return "\n".join(lines)

def formatPemonlist(l:PemonlistLevel,compact:bool=False,exclude_base_info:bool=False):
    lines:list[str]=[]
    if not exclude_base_info:
        lines.append(f"{l.name} ({l.level_id}) Pemonlist #{l.placement}")
    else:
        line=f"#{l.placement}"
        lines.append(line)
        
    return "\n".join(lines)
    
set_formatters()