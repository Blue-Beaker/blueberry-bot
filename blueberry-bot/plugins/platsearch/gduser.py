import math
import os
import random
import threading
import traceback
import time
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.exception import FinishedException
import nonebot.config
from nonebot import get_driver,require
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment

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

require('bbot_render')
from ..bbot_render import RenderAPI
render_api=RenderAPI(uri=plugin_cfg.render_server_uri)

gduser = on_command("gduser")
@gduser.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser("gduser")
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
    
    await bbot_api.trigger_typing(bot,event)
    
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
        
        img=await render_api.render_player_info(req_id_base+"_base",user.user_name,user.stars,user.moons,user.secret_coins,user.user_coins,user.demons,user.creator_points,f"{c.sumNoAuto()}/{c.sum()}",f"{p.sumNoAuto()}/{p.sum()}",c_demons.sum(),pemons.sum(),**user_info_args)
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
        lines.append(f"Non-demons: {user.classic_levels.sumNoAuto()}/{user.classic_levels.sum()}, Non-pemons: {user.plat_levels.sumNoAuto()}/{user.plat_levels.sum()}")
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

    
async def render_nondemons(req_id:str,classic:gd.PlayerLevels,plat:gd.PlayerLevels):
    return await render_api.render_nondemons(req_id,classic.auto,classic.easy,classic.normal,classic.hard,classic.harder,classic.insane,classic.sum(),plat.auto,plat.easy,plat.normal,plat.hard,plat.harder,plat.insane,plat.sum(),classic.daily,classic.gauntlet)

async def render_demons(req_id:str,classic:gd.PlayerDemonLevels,plat:gd.PlayerDemonLevels):
    return await render_api.render_demons(req_id,classic.ezd,classic.med,classic.hdd,classic.insd,classic.exd,classic.sum(),plat.ezd,plat.med,plat.hdd,plat.insd,plat.exd,plat.sum(),classic.weekly,classic.gauntlet)

def get_help(bot:Bot,event:Event):
    return ["gduser [用户名/ID] 展示玩家信息"]