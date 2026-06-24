from .plat_sheets import PlatChartEntry,TheListsEntry,LevelEntry

def formatDiffChart(l:PlatChartEntry,compact:bool=False,exclude_base_info:bool=False):
    line:list[str]=[]
    if not exclude_base_info:
        line.append(l.name)
        if l.id>=0:
            line.append(f" ({l.id})")
        if l.tier:
            line.append(f"(T{l.tier})")
    if not compact:
        if l.tags:
            line.append(f"\nTags: {','.join(l.tags)}")
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
            line.append("\n"+",".join(rankline))
    else:
        tagstr=','.join(l.tags) if l.tags else ""
        if tagstr.__len__()>15:
            tagstr=tagstr[0:13]+"..."
        line.append(f"\nE{l.enj or '-'},W{l.weight or l.tpl or '-'},P{l.pemon or '-'}")
        line.append(f" {tagstr}")
    
    return "".join(line)

def formatListsLevel(l:TheListsEntry,compact:bool=False,exclude_base_info:bool=False):
    lines:list[str]=[]
    
    if not exclude_base_info:
        firstline=f"{l.name} by {l.creator} ({l.sheet} {l.section})"
    else:
        firstline=f"{l.sheet} {l.section}"
        
    if compact:
        lines.append(firstline)
        if not exclude_base_info and l.id:
            lines.append(f"ID ({l.id})")
        lines.append(f"Checkpoints: {l.checkpoints}, Skillsets: {",".join(l.skillsets)}")
        lines.append(f"Description: {l.description}")
    else:
        line=firstline
        if l.checkpoints:
            line+=f" ◆{l.checkpoints}"
        lines.append(line)
    return "\n".join(lines)