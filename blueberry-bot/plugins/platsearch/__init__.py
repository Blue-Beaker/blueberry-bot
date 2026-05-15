import math
import os
import random
import re
import threading
import time
import traceback
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
import nonebot.config
from nonebot import get_driver
import argparse

from .config import Config

from . import plat_sheets
from .data_cache import BaseCache

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

class ArgumentError(Exception):
    pass

class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        raise ArgumentError(message)

class SearchArgs:
    parser=SafeParser()
    parser.add_argument('-p',type=int,default=1)
    parser.add_argument('-f',action='store_true')
    parser.add_argument('search', nargs='*', type=str, help='search string')
    parser.add_argument('-t',type=int,default=-1)
    parser.add_argument('-s',type=str,default=None)
    
    page:int
    fuzzy:bool
    text:str
    tier:int
    skills:list[str]
    
    def __init__(self,text:str) -> None:
        args=self.parser.parse_args(text.split(" "))
        self.page=args.p
        self.fuzzy=args.f
        self.skills=[t.strip().lower() for t in args.s.split(",")] if args.s else []
        self.text=(" ".join(args.search)).replace("_","-")
        self.tier=args.t

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
    try:
        sa=SearchArgs(args.extract_plain_text())
    except ArgumentError as e:
        await platweight.finish(f"参数解析失败:{e}")
        return
        
    text=sa.text
    
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
    try:
        sa=SearchArgs(args.extract_plain_text())
    except ArgumentError as e:
        await platweight.finish(f"参数解析失败:{e}")
        return
    text=sa.text
    page=sa.page
    
    search = text.strip().lower()
    msg=[]
    
    if not sa.fuzzy:
        msg.append(f"Exact match, use -f [levelname] for fuzzy search")
    # results=level_in_three_sheets(search)
    
    results=search_in_levels(PLAT_SHEET_CACHE.get(),search,sa.fuzzy)
    
    
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
    try:
        sa=SearchArgs(args.extract_plain_text())
    except ArgumentError as e:
        await platweight.finish(f"参数解析失败:{e}")
        return
    text=sa.text
    page=sa.page
    skills=sa.skills
    
    search = text.strip().lower()
    
    msg:list[str]=[]
    
    if not sa.fuzzy:
        msg.append(f"Exact match, use -f [levelname] for fuzzy search")
    # results:list[plat_sheets.PlatChartEntry]=[]
    # levels=plat_sheets.get_plat_chart()
    
    # for l in levels:
    #     if search in l.name.lower():
    #         results.append(l)
    results=search_in_levels(PLAT_CHART_CACHE.get(),search,sa.fuzzy)
    
    if skills:
        results = [r for r in results if r.has_skills(skills)]
    
    if sa.tier>=0:
        results = [r for r in results if r.tier==str(sa.tier)]
    
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
            
            msg.append("".join(line))
        
    await platsearch.send("\n".join(msg))
    
    
platskill = on_command("platskill")
@platskill.handle()
async def _(args: Message = CommandArg()):
    try:
        sa=SearchArgs(args.extract_plain_text())
    except ArgumentError as e:
        await platweight.finish(f"参数解析失败:{e}")
        return
    search=sa.text
    page=sa.page
    
    msg=[]
    # If no args present, list all skillsets
    if not sa.text:
        the_lists=PLAT_SHEET_CACHE.get()
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
    the_lists=PLAT_SHEET_CACHE.get()
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

T = TypeVar("T", bound=Any)
def select_page(results:list[T],count:int,entries_per_page:int,page:int):
    maxpages=1+((count-1)//entries_per_page)
    page=max(1,min(page,maxpages))
    if count>entries_per_page:
        results=results[(page-1)*entries_per_page:min(page*entries_per_page,count)]
    return results,maxpages,page


L = TypeVar("L", bound=plat_sheets.LevelEntry)
def search_in_levels(levels:list[L],search:str,fuzzy:bool=False):
    result:list[L]=[]
    for level in levels:
        if level.matchesName(search,fuzzy):
            result.append(level)
    return result

plathelp = on_command("plathelp")
@plathelp.handle()
async def _():
    help_lines=[
        "plathelp 显示Plat搜索功能相关帮助",
        "platsearch 搜索Plat关卡",
        "platsheet 在NLW/IDS/HDS中搜索Plat关卡",
        "platweight <关卡1>,<关卡2>... 计算Plat关卡的Weight之和",
        "platskill <Skillsets> 根据NLW/IDS/HDS的Skillset标签搜索Plat关卡",
        "加入 -f 以模糊匹配, -p<页数> 以翻页, -t<Tier数> 按Tier过滤",
        "举例: '-platsearch -f -p3 dash' 搜索名称包含dash的关卡, 并翻到第3页",
        "举例: '-platsearch -f -t9' 列举 Tier 9 的关卡",
        "由于搜索参数限制, 关名有-请用_代替",
    ]
    await plathelp.finish("\n".join(help_lines))
    return

def get_help(bot:Bot,event:Event):
    help_lines=[
            "platsearch 搜索Plat关卡",
            "platweight 计算Plat关卡的Weight之和",
            "plathelp 显示Plat搜索功能相关帮助"
            ]
    return help_lines