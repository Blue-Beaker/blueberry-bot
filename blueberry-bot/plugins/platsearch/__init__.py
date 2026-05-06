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

def main():
    platweight = on_command("platweight")
    @platweight.handle()
    async def _(args: Message = CommandArg()):
        sa=SearchArgs(args.extract_plain_text())
        text=sa.text
        page=sa.page
        
        search = text.strip().lower()
        msg=[]
        
        msg.extend(plat_rank_results(search,page))
        
        await platweight.send("\n".join(msg))
        
    platsheet = on_command("platsheet")
    @platsheet.handle()
    async def _(args: Message = CommandArg()):
        sa=SearchArgs(args.extract_plain_text())
        text=sa.text
        page=sa.page
        
        search = text.strip().lower()
        msg=[]
        
        msg.extend(sheets_results(search,page))
            
        await platsheet.send("\n".join(msg))
        
        
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
            
        
        results=skill_in_three_sheets(search)
        
        count=results.__len__()
        entries_per_page = 5
        
        results:list[plat_sheets.LevelEntry]
        results,maxpages,page=select_page(results,count,entries_per_page,page)
            
        if not count:
            msg.append(f"No levels found with skill {search}")
        else:
            msg.append(f"{count} levels found with skills (Page {page}/{maxpages}):")
            msg.extend([f"{l.name} by {l.creator}" for l in results])
        
        await platskill.send("\n".join(msg))

def plat_rank_results(search:str,page:int=1):
    msg=[]
    results=plat_sheets.plat_rank_weight(search)
    count=results.__len__()
    
    entries_per_page = 5
    
    results,maxpages,page=select_page(results,count,entries_per_page,page)
    
    if count==0:
        msg.append("Not found on Plat Rank")
    else:
        msg.append(f"{count} on Plat Rank (Page {page}/{maxpages}):")
        msg.extend(results)
    return msg

def sheets_results(search:str,page:int=1):
    msg=[]
    results=level_in_three_sheets(search)
    count=results.__len__()
    
    entries_per_page = 3
    
    results:list[plat_sheets.LevelEntry]
    results,maxpages,page=select_page(results,count,entries_per_page,page)
        
    if count==0:
        msg.append("Not found on the sheets")
    else:
        msg.append(f"{count} on sheets (Page {page}/{maxpages}):")
        
        for level in results:
            msg.append(f"{level.name} by {level.creator} (in {level.sheet} {level.section}):")
            msg.append(f"Checkpoints: {level.checkpoints}, Skillsets: {",".join(level.skillsets)}")
            msg.append(f"Description: {level.description}")
    return msg

def level_in_three_sheets(search:str):
    result:list[plat_sheets.LevelEntry]=[]
    the_lists=plat_sheets.get_3_lists()
    for level in the_lists:
        if(search in level.name.lower()):
            result.append(level)
    return result

skill_groups=[["dash orbs","wavedash"]]

def skill_in_three_sheets(search:str):
    result:list[plat_sheets.LevelEntry]=[]
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
            
if plugin_config.sheets_api_key:
    main()
else:
    logger.error(f"API key for sheets is not set. Not loading this module")