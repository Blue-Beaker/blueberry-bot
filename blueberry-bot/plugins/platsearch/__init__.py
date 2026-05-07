import random
import traceback
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
import nonebot.config
from nonebot import get_driver

from .config import Config

from . import plat_sheets

# driver=get_driver()

# @driver.on_startup
# def test():
#     logger.info(plat_sheets.get_3_sheets().__str__())
    

plugin_config = get_plugin_config(Config)

class SearchArgs:
    def __init__(self,text:str) -> None:
        self.page=0
        if text.startswith("-"):
            try:
                spl=text.split(" ",1)
                self.page=int(spl[0].removeprefix("-"))
                text=spl[1] if spl.__len__()>=2 else ""
            except:
                pass
        self.text=text

platweight = on_command("platweight")
@platweight.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    text=sa.text
    page=sa.page
    
    search = text.strip().lower()
    msg=[]
    
    results:list[plat_sheets.PlatRankEntry]=[]
    for level in plat_sheets.plat_rank_weights():
        if search in level.name.lower():
            results.append(level)
            
    count=results.__len__()
    entries_per_page = 5
    
    results,maxpages,page=select_page(results,count,entries_per_page,page)
    
    if count==0:
        msg.append("Not found on Plat Rank")
    else:
        msg.append(f"{count} on Plat Rank (Page {page}/{maxpages}):")
        for l in results:
            msg.append(f"{l.name} ({l.section}) Weight:{l.weight}")
    
    await platweight.send("\n".join(msg))
    
platsheet = on_command("platsheet")
@platsheet.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    text=sa.text
    page=sa.page
    
    search = text.strip().lower()
    msg=[]
    
    results=level_in_three_sheets(search)
    count=results.__len__()
    
    entries_per_page = 3
    
    results:list[plat_sheets.TheListsEntry]
    results,maxpages,page=select_page(results,count,entries_per_page,page)
        
    if count==0:
        msg.append("Not found on the sheets")
    else:
        msg.append(f"{count} on sheets (Page {page}/{maxpages}):")
        
        for level in results:
            msg.append(f"{level.name} by {level.creator} ({level.sheet} {level.section}):")
            msg.append(f"Checkpoints: {level.checkpoints}, Skillsets: {",".join(level.skillsets)}")
            msg.append(f"Description: {level.description}")
        
    await platsheet.send("\n".join(msg))


platsearch = on_command("platsearch")
@platsearch.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    text=sa.text
    page=sa.page
    
    search = text.strip().lower()
    
    msg:list[str]=[]
    results:list[plat_sheets.PlatChartEntry]=[]
    levels=plat_sheets.get_plat_chart()
    
    for l in levels:
        if search in l.name.lower():
            results.append(l)
    
    count=results.__len__()
    entries_per_page = 5
    
    results,maxpages,page=select_page(results,count,entries_per_page,page)
    
    if not count:
        msg.append(f"Not found")
    else:
        msg.append(f"{count} found (Page {page}/{maxpages}):")
        for l in results:
            line:list[str]=[l.name]
            if l.id>=0:
                line.append(f" ({l.id})")
            line.append(f"(T{l.tier})")
            if l.tags:
                line.append(f"\nTags: {','.join(l.tags)}")
            if l.tpl or l.pemon:
                line.append(f"\nTPL: {l.tpl}, Pemonlist: {l.pemon}")
            line.append(f"")
            
            msg.append("".join(line))
        
    await platsearch.send("\n".join(msg))
    
    
platskill = on_command("platskill")
@platskill.handle()
async def _(args: Message = CommandArg()):
    sa=SearchArgs(args.extract_plain_text())
    search=sa.text
    page=sa.page
    
    msg=[]
    # If no args present, list all skillsets
    if not sa.text:
        the_lists=plat_sheets.get_3_lists()
        skills=[]
        for l in the_lists:
            for s in l.skillsets:
                if s not in skills:
                    skills.append(s)
        msg.append(f"There are {skills.__len__()} skills.")
        msg.append(f"Use '-platskill skill1,skill2...' to filter levels by skillsets.")
        msg.append(f"Example: -platskill {random.choice(skills)}")
        await platskill.send("\n".join(msg))
        return
        
    
    results:list[plat_sheets.TheListsEntry]=skill_in_three_sheets(search)
    
    count=results.__len__()
    entries_per_page = 5
    
    results,maxpages,page=select_page(results,count,entries_per_page,page)
        
    if not count:
        msg.append(f"No levels found with skill {search}")
    else:
        msg.append(f"{count} levels found with skills (Page {page}/{maxpages}):")
        msg.extend([f"{l.name} by {l.creator}" for l in results])
    
    await platskill.send("\n".join(msg))

def level_in_three_sheets(search:str):
    result:list[plat_sheets.TheListsEntry]=[]
    the_lists=plat_sheets.get_3_lists()
    for level in the_lists:
        if(search in level.name.lower()):
            result.append(level)
    return result

skill_groups=[["dash orbs","wavedash"]]

def skill_in_three_sheets(search:str):
    result:list[plat_sheets.TheListsEntry]=[]
    the_lists=plat_sheets.get_3_lists()
    split:list[str]=[t.strip().lower() for t in search.split(",")]
    
    for level in the_lists:
        lskills=[s.lower() for s in level.skillsets]
        for group in skill_groups:
            intersect=list(set(group) & set(lskills))
            if intersect:
                lskills=list(set(group) | set(lskills))
        matched=True
        for s in split:
            if s not in lskills:
                matched=False
                break
        if matched:
            result.append(level)
    return result

def select_page(results:list,count:int,entries_per_page:int,page:int):
    maxpages=1+((count-1)//entries_per_page)
    page=max(1,min(page,maxpages))
    if count>entries_per_page:
        results=results[(page-1)*entries_per_page:min(page*entries_per_page,count)]
    return results,maxpages,page