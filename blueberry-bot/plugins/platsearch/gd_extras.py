import math
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
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment

from . import godot_draw
from .config import Config
from .gd_icon import IconType, construct_icon_url,get_icon,ICON_TYPES

require('bbot_api')
from .. import bbot_api
from ..bbot_api.argparse import ArgumentError,ArgParser
require('gd_api')
from ..gd_api.gd import getLevel2,getList2,getUser,getLevelsFromList,ListSearchType,LevelSearchType,PlayerIcons
from ..gd_api import gd
from ..gd_api.thumbs import getThumbnail

driver=get_driver()
plugin_cfg=get_plugin_config(Config)

render_api=godot_draw.RenderAPI()
render_api.uri=plugin_cfg.render_server_uri

gdlist = on_command("gdlist")
@gdlist.handle()
async def _(args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parser.add_argument('-u',help="Search User's Lists",action='store_true')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 1
        fromuser=bool(parsed.u)
        
    except Exception as e:
        await gdlist.finish(str(e))
        return
    
    lines:list[str]=[]
    
    searchType:gd.ListSearchType=gd.ListSearchType.SEARCH
    
    if fromuser:
        searchType=gd.ListSearchType.FROM_USER
        user=getUser(search)
        if not user:
            lines.append("未找到指定用户.")
            await gdlist.finish("\n".join(lines))
            return
        search=str(user.account_id)
    
    listID = None
    if searchType==gd.ListSearchType.SEARCH:
        try:
            listID = int(search)
        except:
            pass
    
    if listID is not None:
        page_size=10
        lists,pageinfo=getList2(search,page-1)
        if not lists:
            lines.append("没有查找到List.")
            await gdlist.finish("\n".join(lines))
        levels = getLevelsFromList(listID)
        if not levels:
            lines.append("List为空.")
            await gdlist.finish("\n".join(lines))
        
        count=levels.__len__()
        max_page=math.ceil(count/page_size)
        
        page=min(page,max_page)
        start=(page-1)*page_size
        
        levels=levels[start:min(start+page_size,count)]
        
        l=lists[0]
        lines.append(repr_list(l,False))
        lines.append(f"{page}/{math.ceil(count/page_size)}页 ({start+1}-{min(start+page_size,count)} of {count})")
        lines.append(f"-gdlist -p <页数> <ListID> 以翻页.")
        
        for l in levels:
            lines.append(repr_level(l))
            
        await gdlist.finish("\n".join(lines))
        
    else:   
        lists,pageinfo=getList2(search,page-1,searchType=searchType)
        
        if lists.__len__()==0 or not pageinfo:
            lines.append("没有查找到任何List.")
        elif lists.__len__()>1:
            lines.append(f"第 {page}/{math.ceil(pageinfo.total/pageinfo.amount)} 页 ({pageinfo.offset}-{pageinfo.offset+pageinfo.amount}/{pageinfo.total})")
            for l in lists:
                lines.append(repr_list(l,fromuser))
            await gdlist.finish("\n".join(lines))
            return
        l=lists[0]
        lines.append(repr_list(l,fromuser))
        lines.append(f"-gdlist {l.id} 以查看list内容.")
        
        await gdlist.finish("\n".join(lines))
    

gdthumb = on_command("gdthumb")
@gdthumb.handle()
async def _(bot:OBBot|DCBot,args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('-a',help='Include Unrated',action='store_true')
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=parsed.p or 1
        rated=not parsed.a
        
    except Exception as e:
        await gdthumb.finish(str(e))
        return
    
    lines:list[str]=[]
    levels,pageinfo=getLevel2(search,page-1,rated)
    if not isinstance(levels,list):
        await gdthumb.finish("查找出错.")
        return
    if levels.__len__()==0:
        await gdthumb.finish("没有查找到任何关卡.")
        return
    elif levels.__len__()>1 and pageinfo:
        lines.append("找到多个关卡,请用id选择:")
        lines.append(f"第 {page}/{math.ceil(pageinfo.total/pageinfo.amount)} 页 ({pageinfo.offset}-{pageinfo.offset+pageinfo.amount}/{pageinfo.total})")
        for l in levels:
            lines.append(repr_level(l))
        await gdthumb.finish("\n".join(lines))
        return
    
    l=levels[0]
    thumb=getThumbnail(l.id)
    if not thumb:
        await gdthumb.finish(f"未找到该关卡截图: {l.name} by {l.creator} ({l.repr_difficulty()})")
        return
    else:
        await gdthumb.finish(buildMessageImage(bot,f"{l.name} by {l.creator} ({l.repr_difficulty()})",thumb,f"{l.id}.png"))
        return
    
gduser = on_command("gduser")
@gduser.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser()
        parser.add_argument('-c',help='Show Classic breakdown',action='store_true')
        parser.add_argument('-p',help='Show Platformer breakdown',action='store_true')
        parser.add_argument('-d',help='Show Demons breakdown',action='store_true')
        parser.add_argument('-v',help='Show Other Info',action='store_true')
        parser.add_argument('-t',help='Plain Text',action='store_true')
        parser.add_argument('-i',help='Show Icons',action='store_true')
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parsed=parser.parse_args(raw_args)
        search=" ".join(parsed.search)
        show_classic=bool(parsed.c)
        show_plat=bool(parsed.p)
        show_demons=bool(parsed.d)
        show_other=bool(parsed.v)
        force_text=bool(parsed.t)
        show_icons=bool(parsed.i)
        
    except Exception as e:
        await gduser.finish(str(e))
        return
    
    lines:list[str]=[]
    
    user=getUser(search)
    if not user or not user.account_id:
        await gduser.finish("未找到玩家, 或发生错误.")
        
    supports_image=(isinstance(bot,OBBot) or isinstance(bot,DCBot))
    enable_image=(not force_text) and supports_image
    
    msg=bbot_api.TextImageMessage.build(bot)
    
    c=user.classic_levels
    p=user.plat_levels
    c_demons=user.classic_demons
    pemons=user.plat_demons
    
    info_image=False
    nondemon_image=False
    demon_image=False
    
    icon=user.icon
    
    # Image Sections
    if enable_image:
        req_id_base=bbot_api.getid(event)
        user_info_args:dict[str,str]={}
        
        player_icons=getIconIDs(user.icon)
        icon_type=ICON_TYPES[icon.icon_type]
        
        user_info_args["player_icon"]=construct_icon_url(icon_type,player_icons.get(icon_type,0),icon.color,icon.color2,icon.glow_color)
        
        if show_icons:
            for i,id in player_icons.items():
                user_info_args["icon_"+i.value]=construct_icon_url(i,id,icon.color,icon.color2,icon.glow_color)
        
        img=await render_api.render_player_info(req_id_base+"_base",user.user_name,user.stars,user.moons,user.secret_coins,user.user_coins,user.demons,user.creator_points,c.sum(),p.sum(),c_demons.sum(),pemons.sum(),**user_info_args)
        if isinstance(img,bytes):
            msg.addImage(img)
            info_image=True
        if show_classic or show_plat:
            img=await render_nondemons(req_id_base+"_nondemon",c,p)
            if isinstance(img,bytes):
                msg.addImage(img)
                nondemon_image=True
        if show_demons:
            img=await render_demons(req_id_base+"_demon",c_demons,pemons)
            if isinstance(img,bytes):
                msg.addImage(img)
                demon_image=True
            
    # Basic Info (Text)
    if not info_image:
        lines.append(f"{user.user_name}")
        stats_line=f"{user.stars}⭐ {user.moons}🌙 {user.secret_coins}✪ {user.user_coins}© {user.demons}😈 {user.diamonds}💎"
        if user.creator_points:
            stats_line+=f"{user.creator_points}🛠"
        lines.append(stats_line)
        lines.append(f"Non-demons: {user.classic_levels.sum()}, Non-pemons: {user.plat_levels.sum()}")
        lines.append(f"Demons: {c_demons.sum()}, Pemons: {pemons.sum()}")
    
    if not (show_classic or show_plat or show_demons):
        lines.append("使用-c、-p、-d参数, 可显示Classic、Plat与Demon关卡的详细计数")
        
    if not nondemon_image:
        # Nondemons (Text)
        def format_nondemons(l:gd.PlayerLevels):
            return f"{l.auto}🤖 {l.easy}😃 {l.normal}🙂 {l.hard}🙁, {l.harder}😡, {l.insane}😫"
        if show_classic:
            lines.append(f"Classic: ")
            lines.append(format_nondemons(user.classic_levels))
            lines.append(f"Daily: {c.daily} Gauntlets: {c.gauntlet}")
        if show_plat:
            lines.append(f"Plat: ")
            lines.append(format_nondemons(user.plat_levels))
    
    # Demons (Text)
    if (not demon_image) and show_demons:
        lines.append(f"{c_demons.ezd}EZD {c_demons.med}MED {c_demons.hdd}HDD {c_demons.insd}INSD {c_demons.exd}EXD")
        lines.append(f"{pemons.ezd}EZP {pemons.med}MEP {pemons.hdd}HDP {pemons.insd}INSP {pemons.exd}EXP")
        lines.append(f"Weekly: {c_demons.weekly} Gauntlets: {c_demons.gauntlet}")
    
    # Others (Text)
    if show_other:
        lines.append(f"Global Rank {user.global_rank}")
        lines.append(f"Account ID {user.account_id}")
        lines.append(f"Player ID {user.user_id}")
        
    if show_icons and supports_image and not enable_image:
        icon_type=ICON_TYPES[icon.icon_type]
        icon_id=icon.get_icon_for_type(icon_type.value) or 0
        url=construct_icon_url(icon_type,icon_id,icon.color,icon.color2,icon.glow_color)
        
        logger.info(url)
        icon=get_icon(icon_type,icon_id,icon.color,icon.color2,icon.glow_color)
        if icon:
            msg.addImage(icon,"icon.png",True)
        
    msg.addText("\n".join(lines))
    await gduser.finish(msg.msg)
    
def getIconIDs(icon: PlayerIcons):
    id_for_types:dict[IconType,int]={}
    for i in IconType:
        id_for_types[i]=icon.get_icon_for_type(i.value) or 0
    return id_for_types
    
def buildMessageImage(bot:Bot,message:str,image:bytes,image_name:str):
    if isinstance(bot,OBBot):
        return(OBMessageSegment.text(message)+OBMessageSegment.image(image))
    else:
        return(DCMessage().append(message).append(DCMessageSegment.attachment(image_name,content=image)))

def get_help(bot:Bot,event:Event):
    if isinstance(bot,OBBot) or isinstance(bot,DCBot):
        return ["gdthumb [关名/ID] 获取关卡截图",
                "gduser [用户名/ID] 展示玩家信息"]
    else:
        return ["gduser [用户名/ID] 展示玩家信息"]
    
def repr_level(l:gd.Level,fromuser:bool=False):
    return f"{l.id} = {l.name} by {l.creator} ({l.repr_difficulty()})" if not fromuser else f"{l.id} = {l.name} ({l.repr_difficulty()})"

def repr_list(l:gd.LevelList,fromuser:bool=False):
    return f"{l.name} by {l.creator} ({l.id}) ({l.levels.__len__()} 个关卡)" if not fromuser else f"{l.name} ({l.id}) ({l.levels.__len__()} 个关卡)"
    
async def render_nondemons(req_id:str,classic:gd.PlayerLevels,plat:gd.PlayerLevels):
    return await render_api.render_nondemons(req_id,classic.auto,classic.easy,classic.normal,classic.hard,classic.harder,classic.insane,classic.sum(),plat.auto,plat.easy,plat.normal,plat.hard,plat.harder,plat.insane,plat.sum(),classic.daily,classic.gauntlet)

async def render_demons(req_id:str,classic:gd.PlayerDemonLevels,plat:gd.PlayerDemonLevels):
    return await render_api.render_demons(req_id,classic.ezd,classic.med,classic.hdd,classic.insd,classic.exd,classic.sum(),plat.ezd,plat.med,plat.hdd,plat.insd,plat.exd,plat.sum(),classic.weekly,classic.gauntlet)