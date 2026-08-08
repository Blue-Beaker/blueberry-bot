import time
from nonebot import on_command,logger,get_plugin_config
from nonebot import get_driver,require
from nonebot.params import CommandArg
from nonebot.internal.matcher import Matcher
from nonebot.adapters import Message,Event,Bot

require("bbot_api")
from ..bbot_api.argparse import ArgParser
from ..bbot_api.message_compat import file

from .plat_rank_data import PlatRankPlayer
from .gd_data import PLAT_RANK_CACHE,PLAT_CHART_CACHE
from .data_cache import KeyMapCache
from .utils import select_page
from .plat_sheets import PlatChartEntry
from .formatters import formatDiffChart

platrank = on_command("platrank")
@platrank.handle()
async def _(bot:Bot,args: Message = CommandArg()):
    parser=ArgParser("platrank")
    parser.add_argument("username",type=str,nargs="*")
    parser.add_argument("-f",help="Fuzzy Search",action='store_true')
    parser.add_argument('-p',help="Page",type=int,default=1)
    parser.add_argument('--pagesize',help="Page Size",type=int,default=5)
    
    if args.extract_plain_text().__len__()==0:
        await platrank.finish(parser.format_help())
    try:
        parsed=parser.parse_args(args.extract_plain_text().split(" "))
        search=str(" ".join(parsed.username))
        fuzzy=bool(parsed.f)
        page=int(parsed.p)
        pagesize=int(parsed.pagesize)
        
    except Exception as e:
        await platrank.finish(str(e))
        
    entries=PLAT_RANK_CACHE.get()
    
    results:list[PlatRankPlayer]=[p for p in entries if p.matchesName(search,fuzzy)]
    
    count=results.__len__()
    
    results,maxpages,page=select_page(results,count,pagesize,page)
    
    msg=[]
    
    if count==0:
        msg.append("Not found")
    else:
        msg.append(f"{count} found (Page {page}/{maxpages}):")
        
        for player in results:
            msg.append(formatPRPlayer(player,count>1))
    
    finalmsg="\n".join(msg)
    
    if results.__len__()>50:
        send_file=file(bot,finalmsg.encode(),f"platrank_result_{time.time()//1}.txt")
        if not isinstance(send_file,str):
            await platrank.finish(send_file)
    await platrank.finish(finalmsg)
            
def plat_chart_name(e:PlatChartEntry):
    return e.name.lower().strip()
PLAT_CHART_NAMES = KeyMapCache(plat_chart_name)
PLAT_CHART_CACHE.add_keymap(PLAT_CHART_NAMES)

            
def formatPRPlayer(p:PlatRankPlayer,compact:bool=False,exclude_base_info:bool=False):
    lines:list[str]=[]
    
    if not exclude_base_info:
        firstline=f"{p.name} #{p.ranking} {p.points}"
    else:
        firstline=f"#{p.ranking} {p.points}"
        
    if not compact:
        lines.append(firstline)
        lines.append(f"Hardest Levels: ")
        for i in range(len(p.hardest_levels)):
            l=p.hardest_levels[i]
            level=PLAT_CHART_NAMES.get(l.lower().strip())
            if level:
                level0=level[0]
                lines.append(f"  #{i+1} {l} W{level0.weight or "-"}/{(level0.weight_type or "-")[0]} P{level0.pemon or "-"}")
            else:
                lines.append(f"  #{i+1} {l}")
        if len(p.verifications)>0:
            lines.append(f"Verifications: {','.join(p.verifications)}")
        if len(p.first_victors)>0:
            lines.append(f"First Victors: {','.join(p.first_victors)}")
        return "\n".join(lines)
    else:
        return firstline