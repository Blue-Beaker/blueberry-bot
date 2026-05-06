import json
import traceback
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot as MCBot
from nonebot.adapters.minecraft import BaseChatEvent,MessageEvent,NoticeEvent,BaseJoinEvent,BaseQuitEvent
from nonebot.adapters.discord.bot import Bot as DCBot
from nonebot.adapters.discord import Adapter as DCAdapter
from nonebot.adapters.discord.api import Snowflake
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
import nonebot.config
from nonebot import get_driver

from .config import Config

from .sheets_api import Sheets

# The ID and range of a sample spreadsheet.
PLAT_RANK_SPREADSHEET = "1uicngbhpej4PEmtYYeGmYlFsA28PwTzzouWb4EWQkTY"
WEIGHT_RANGE = "Weight!A2:E"

plugin_config = get_plugin_config(Config)
driver = get_driver()

sheets:Sheets = Sheets()

@driver.on_startup
async def init_api():
    sheets.init_api()

platsearch = on_command("platsearch")
@platsearch.handle()
async def _(args: Message = CommandArg()):
    search = args.extract_plain_text().strip().lower()
    msg=[]
    results=search_plat_rank_weight(search)
    count=results.__len__()
    if count>5:
        results=results[0:5]
    
        
    if not results:
        msg.append("Not found on Plat Rank")
    else:
        msg.append(f"{count} levels found on Plat Rank:")
        msg.extend(results)
        
    await platsearch.send("\n".join(msg))
    
    
def search_plat_rank_weight(search:str):
    results=[]
    values=sheets.get(PLAT_RANK_SPREADSHEET,WEIGHT_RANGE)
    
    if values:
        current_section=""
        for line in values:
            level=line[0]
            weight=line[1]
            if not weight:
                current_section=level.removesuffix("Placements").strip()
                continue
            
            misc_place=[i.strip() for i in line[2].split(",")]
            pemonlist_place=[i.strip() for i in line[3].split(",")]
            
            matched=False
            
            if search in level.lower():
                matched=level
                
            if matched:
                results.append(f"{matched} ({current_section}) Weight:{weight}")
    return results