import os
import random
import threading
import time
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
import nonebot.config
from nonebot import get_driver,require

from .config import Config

from . import plat_sheets
from .data_cache import BaseCache
from .utils import select_page

require('bbot_api')
from ..bbot_api.argparse import ArgumentError,ArgParser

from . import underrated

from . import gd_extras

plugin_config = get_plugin_config(Config)

driver=get_driver()

PLAT_CHART_CACHE=BaseCache(plat_sheets.PlatChartEntry,"platsearch_cache/plat_chart_cache.json",
                           plugin_config.sheets_update_interval).set_update_function(plat_sheets.get_plat_chart)
PLAT_SHEET_CACHE=BaseCache(plat_sheets.TheListsEntry,"platsearch_cache/plat_sheet_cache.json",
                           plugin_config.sheets_update_interval).set_update_function(plat_sheets.get_3_lists)

@driver.on_startup
async def load_cache():
    os.makedirs("platsearch_cache",exist_ok=True)
    threading.Thread(target=threaded_update_cache,args=[PLAT_CHART_CACHE,"Plat Chart cache"]).start()
    threading.Thread(target=threaded_update_cache,args=[PLAT_SHEET_CACHE,"Plat Sheet cache"]).start()

def threaded_update_cache(cache:BaseCache,name:str):
    cache.get()
    logger.info(f"Loaded {cache.entries.__len__()} entries into {name}, expiring at {time.ctime(cache.expiration_time)}")

class SearchArgs:
    parser=ArgParser()
    parser.add_argument('-p',help="Page",type=int,default=1)
    parser.add_argument('-f',help="Fuzzy Search",action='store_true')
    parser.add_argument('search', nargs='*', type=str, help='search string')
    parser.add_argument('-t',help="Tier",type=str,default="")
    parser.add_argument('-s',help="Skills",type=str,default=None)
    
    page:int
    fuzzy:bool
    text:str
    tier:str
    skills:list[str]
    error:str|None=None
    
    def __init__(self) -> None:
        self.page=1
        self.fuzzy=False
        self.skills=[]
        self.text=""
        self.tier=""
        
    def parse(self,text:str):
        try:
            args=self.parser.parse_args(text.split(" "))
            self.page=args.p
            self.fuzzy=args.f
            self.skills=[t.strip().lower() for t in args.s.split(",")] if args.s else []
            self.text=(" ".join(args.search)).replace("_","-")
            self.tier=args.t
        except Exception as e:
            self.error=str(e)
        return self

def get_weight_factors():
    factor=0.2**(1/9)
    weight_factors=[]
    for i in range(0,10):
        weight_factors.append(1*(factor**i))
    return weight_factors
WEIGHT_FACTORS=get_weight_factors()

platweight = on_command("platweight")
@platweight.handle()
async def _(args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        text=" ".join(parsed.search)
    except Exception as e:
        await platweight.finish(str(e))
        return
    
    search = [s.strip() for s in text.lower().split(",")]
    
    msg=[]
    results:list[plat_sheets.PlatChartEntry]=[]
    errored:bool=False
    for s in search:
        levels=[l for l in PLAT_CHART_CACHE.get() if (l.exactMatch(s) or str(l.id)==s) and l.weight]
        if levels.__len__()==1:
            results.append(levels[0])
            continue
        elif levels.__len__()==0:
            errored=True
            msg.append(f"没有找到'{s}'的权重,请更正或移除.")
        else:
            errored=True
            msg.append(f"'{s}' 找到{levels.__len__()}个结果, 请改用关卡ID:")
            for l in levels:
                results.append(l)
                msg.append(f"({l.id}) {l.name} by {l.creator} ({l.weight})")
    if errored:
        msg.append("请解决上述问题再重新运行本指令.")
        await platweight.finish("\n".join(msg))
        return
    
    def sortWeight(l:plat_sheets.PlatChartEntry):
        return l.weight or float('inf')
    
    results.sort(key=sortWeight)
    
    if results.__len__()==10:
        top10_weight=0
        total_weight=0
        weights:list[int]=[l.weight for l in results if l.weight]
        # weight_factors=[1,0.84,0.7,0.58,0.49,0.41,0.34,0.29,0.24,0.2]
        for i in range(0,10):
            r=results[i]
            factored_weight=weights[i]*WEIGHT_FACTORS[i]
            msg.append(f"{r.name} by {r.creator} ({r.weight}*{WEIGHT_FACTORS[i]:.2f}={factored_weight:.2f})")
            top10_weight+=factored_weight
            total_weight+=weights[i]
        msg.append(f"你的点数为{top10_weight:.2f}, 原始权重和为{total_weight}")
    else:
        total_weight=0
        for r in results.copy():
            if not r.weight:
                continue
            try:
                msg.append(f"{r.name} by {r.creator} ({r.weight})")
                total_weight+=r.weight
            except:
                results.remove(r)
                pass
        msg.append(f"{results.__len__()} 项的原始权重和为 {total_weight}.\n提供10项以计算你的点数.")
    
    
    await platweight.finish("\n".join(msg))
    
platsheet = on_command("platsheet")
@platsheet.handle()
async def _(args: Message = CommandArg()):
    if not args.extract_plain_text().strip():
        await platsheet.finish("\n".join(
            [
                "用法: -platsheet [参数] <关名/ID>"
                "加入 -f 以模糊匹配, -p<页数> 以翻页",
                "-t<Tier数> 按Tier过滤, -s<Tags> 按Skillset过滤(自动启用模糊匹配)",
                "举例: '-platsheet -p3 -s dash' 搜索名称包含dash的关卡, 并翻到第3页",
                "举例: '-platsheet -t easy -s wavedash' 列举 Easy 且包含 wavedash skill 的关卡"
                ]))
        
    sa=SearchArgs().parse(args.extract_plain_text())
    if sa.error:
        await platweight.finish(sa.error)
        return
    text=sa.text
    page=sa.page
    skills=sa.skills
    tier=sa.tier.lower()
    fuzzy=sa.fuzzy
    
    if tier or skills:
        fuzzy=True
        
    search = text.strip().lower()
    msg=[]
    
    if not fuzzy:
        msg.append(f"Exact match, use -f [levelname] for fuzzy search")
    # results=level_in_three_sheets(search)
    
    results=[l for l in PLAT_SHEET_CACHE.get() if l.matchesName(search,fuzzy)]
    
    if skills:
        results = [r for r in results if r.has_skills(skills)]
    if tier:
        results = [r for r in results if r.section.lower()==tier]
        
    count=results.__len__()
    
    entries_per_page = 5
    
    results:list[plat_sheets.TheListsEntry]
    results,maxpages,page=select_page(results,count,entries_per_page,page)
        
    if count==0:
        msg.append("Not found on the sheets")
    else:
        msg.append(f"{count} on sheets (Page {page}/{maxpages}):")
        
        for level in results:
            if count<=3:
                msg.append(f"{level.name} by {level.creator} ({level.sheet} {level.section}):")
                msg.append(f"Checkpoints: {level.checkpoints}, Skillsets: {",".join(level.skillsets)}")
                msg.append(f"Description: {level.description}")
            else:
                line=f"{level.name} by {level.creator} ({level.sheet} {level.section})"
                if level.checkpoints:
                    line+=f" ◆{level.checkpoints}"
                msg.append(line)
        
    await platsheet.send("\n".join(msg))


platsearch = on_command("platsearch")
@platsearch.handle()
async def _(args: Message = CommandArg()):
    if not args.extract_plain_text().strip():
        await platsearch.finish("\n".join(
            [
                "用法: -platsearch [参数] <关名/ID>"
                "加入 -f 以模糊匹配, -p<页数> 以翻页",
                "-t<Tier数> 按Tier过滤, -s<Tags> 按Tag过滤(自动启用模糊匹配)",
                "举例: '-platsearch -f -p3 dash' 搜索名称包含dash的关卡, 并翻到第3页",
                "举例: '-platsearch -t9' 列举 Tier 9 的关卡"
                ]))
    sa=SearchArgs().parse(args.extract_plain_text())
    if sa.error:
        await platweight.finish(sa.error)
        return
    text=sa.text
    page=sa.page
    skills=sa.skills
    tier=sa.tier
    fuzzy=sa.fuzzy
    
    search = text.strip().lower()
    
    if tier or skills:
        fuzzy=True
    
    msg:list[str]=[]
    
    if not fuzzy:
        msg.append(f"Exact match, use -f [levelname] for fuzzy search")
    # results:list[plat_sheets.PlatChartEntry]=[]
    # levels=plat_sheets.get_plat_chart()
    
    # for l in levels:
    #     if search in l.name.lower():
    #         results.append(l)
    # results=search_in_levels(PLAT_CHART_CACHE.get(),search,fuzzy)
    results=[l for l in PLAT_CHART_CACHE.get() if (l.matchesName(search,fuzzy) or str(l.id)==search)]
    
    if skills:
        results = [r for r in results if r.has_skills(skills)]
    
    if tier:
        results = [r for r in results if r.tier==str(tier)]
    
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
            if l.tier:
                line.append(f"(T{l.tier})")
            if count<=3:
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
                
            msg.append("".join(line))
        
    await platsearch.send("\n".join(msg))
    
    
# platskill = on_command("platskill")
# @platskill.handle()
# async def _(args: Message = CommandArg()):
#     sa=SearchArgs().parse(args.extract_plain_text())
#     if sa.error:
#         await platweight.finish(sa.error)
#         return
#     search=sa.text
#     page=sa.page
    
#     msg=[]
#     # If no args present, list all skillsets
#     if not sa.text:
#         the_lists=PLAT_SHEET_CACHE.get()
#         skills=[]
#         for l in the_lists:
#             for s in l.skillsets:
#                 if s not in skills:
#                     skills.append(s)
#         msg.append(f"There are {skills.__len__()} skills.")
#         msg.append(f"Use '-platskill skill1,skill2...' to filter levels by skillsets.")
#         msg.append(f"Example: -platskill {random.choice(skills)}")
#         await platskill.send("\n".join(msg))
#         return
        
    
#     results:list[plat_sheets.TheListsEntry]=skill_in_three_sheets(search)
    
#     count=results.__len__()
#     entries_per_page = 5
    
#     results,maxpages,page=select_page(results,count,entries_per_page,page)
        
#     if not count:
#         msg.append(f"No levels found with skill {search}")
#     else:
#         msg.append(f"{count} levels found with skills (Page {page}/{maxpages}):")
#         msg.extend([f"{l.name} by {l.creator}" for l in results])
    
#     await platskill.send("\n".join(msg))

def level_in_three_sheets(search:str):
    result:list[plat_sheets.TheListsEntry]=[]
    the_lists=plat_sheets.get_3_lists()
    for level in the_lists:
        if(search in level.name.lower()):
            result.append(level)
    return result

# def skill_in_three_sheets(search:str):
#     result:list[plat_sheets.TheListsEntry]=[]
#     the_lists=PLAT_SHEET_CACHE.get()
#     split:list[str]=[t.strip().lower() for t in search.split(",")]
    
#     for level in the_lists:
#         lskills=[s.lower() for s in level.skillsets]
#         for group in skill_groups:
#             intersect=list(set(group) & set(lskills))
#             if intersect:
#                 lskills=list(set(group) | set(lskills))
#         matched=True
#         for s in split:
#             if s not in lskills:
#                 matched=False
#                 break
#         if matched:
#             result.append(level)
#     return result

# L = TypeVar("L", bound=plat_sheets.LevelEntry)
# def search_in_levels(levels:list[L],search:str,fuzzy:bool=False):
#     result:list[L]=[]
#     for level in levels:
#         if level.matchesName(search,fuzzy):
#             result.append(level)
#     return result

plathelp = on_command("plathelp")
@plathelp.handle()
async def _():
    help_lines=[
        "plathelp 显示Plat搜索功能相关帮助",
        "platsearch 搜索Plat关卡",
        "platsheet 在NLW/IDS/HDS中搜索Plat关卡",
        "platweight <关卡1>,<关卡2>... 计算Plat关卡的Weight之和",
        "加入 -f 以模糊匹配, -p<页数> 以翻页",
        "由于搜索参数限制, 关名有-请用_代替",
    ]
    await plathelp.finish("\n".join(help_lines))
    return


platupdate = on_command("platupdate",permission=SUPERUSER)
@platupdate.handle()
async def _():
    await platupdate.send("开始刷新platsearch缓存...\n刷新DifficultyChart...")
    PLAT_CHART_CACHE.update()
    await platupdate.send("刷新NLW/IDS/HDS...")
    PLAT_SHEET_CACHE.update()
    await platupdate.finish(f"刷新完毕. DifficultyChart:{PLAT_CHART_CACHE.entries.__len__()}, NLW/IDS/HDS:{PLAT_SHEET_CACHE.entries.__len__()})")
    return

def get_help(bot:Bot,event:Event):
    help_lines=[
            "platsearch 搜索Plat关卡",
            "platweight 计算Plat关卡的Weight之和",
            "plathelp 显示Plat搜索功能相关帮助"
            ]
    help_lines.extend(gd_extras.get_help(bot,event))
    return help_lines