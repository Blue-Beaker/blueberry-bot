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

def main():
    platsearch = on_command("platsearch")
    @platsearch.handle()
    async def _(args: Message = CommandArg()):
        search = args.extract_plain_text().strip().lower()
        msg=[]
        
        msg.extend(plat_rank_results(search))
        
        msg.extend(sheets_results(search))
            
        await platsearch.send("\n".join(msg))
        
        
    platskill = on_command("platskill")
    @platskill.handle()
    async def _(args: Message = CommandArg()):
        search = args.extract_plain_text().strip().lower()
        msg=[]
        
        results=skill_in_three_sheets(search)
        count=results.__len__()
        if count>10:
            results=results[0:10]
            
        if not results:
            msg.append(f"Not levels found with skill {search}")
        else:
            msg.append(f"{count} levels found with skills:")
            msg.extend([f"{l.name} by {l.creator}" for l in results])
        
        await platskill.send("\n".join(msg))

def plat_rank_results(search:str):
    msg=[]
    results=plat_sheets.plat_rank_weight(search)
    count=results.__len__()
    if count>5:
        results=results[0:5]
    
    if not results:
        msg.append("Not found on Plat Rank")
    else:
        msg.append(f"{count} levels found on Plat Rank:")
        msg.extend(results)
    return msg

def sheets_results(search:str):
    msg=[]
    sheets_levels=level_in_three_sheets(search)
    sheets_count=sheets_levels.__len__()
    if sheets_count>3:
        sheets_levels=sheets_levels[0:3]
        
    if not sheets_count:
        msg.append("Not found on the sheets")
    else:
        msg.append(f"{sheets_count} levels found on sheets:")
        
        for level in sheets_levels:
            msg.append(f"{level.name} by {level.creator} (in {level.sheet} {level.section}):")
            msg.append(f"Checkpoints: {level.checkpoints}, Skillsets: {level.skillsets}")
            msg.append(f"Description: {level.description}")
    return msg

def level_in_three_sheets(search:str):
    result:list[plat_sheets.LevelEntry]=[]
    the_lists=plat_sheets.get_3_lists()
    for level in the_lists:
        if(search in level.name.lower()):
            result.append(level)
    return result

def skill_in_three_sheets(search:str):
    result:list[plat_sheets.LevelEntry]=[]
    the_lists=plat_sheets.get_3_lists()
    for level in the_lists:
        for skill in level.skillsets:
            if search == skill.strip().lower():
                result.append(level)
    return result
            
if plugin_config.sheets_api_key:
    main()
else:
    logger.error(f"API key for sheets is not set. Not loading this module")