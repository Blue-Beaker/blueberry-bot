import math
import traceback
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.exception import FinishedException
from nonebot import get_driver,require
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment

from .config import Config

require('bbot_api')
from .. import bbot_api
from ..bbot_api.argparse import ArgumentError,ArgParser
require('gd_api')
from ..gd_api.gd import getLevel2,getList2,getUser,getLevelsFromList,ListSearchType,LevelSearchType,PlayerIcons,PageInfo
from ..gd_api import gd
from ..gd_api.thumbs import getThumbnail

driver=get_driver()
plugin_cfg=get_plugin_config(Config)

require('bbot_render')
from ..bbot_render import RenderAPI
render_api=RenderAPI()
render_api.uri=plugin_cfg.render_server_uri

gdlist = on_command("gdlist")
@gdlist.handle()
async def _(bot:Bot, event:Event, args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser("gdlist")
        parser.add_argument('-p',help='Page',type=int)
        parser.add_argument('search', nargs='*', type=str, help='search string')
        parser.add_argument('-u',help="Search User's Lists",action='store_true')
        parsed=parser.parse_args(raw_args)
        
        search=" ".join(parsed.search)
        page=int(parsed.p or 1)
        fromuser=bool(parsed.u)
        
    except Exception as e:
        await gdlist.finish(str(e))
        return
    try:
        lines:list[str]=[]
        
        await bbot_api.trigger_typing(bot,event)
        
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
            
            lines.append(repr_list(lists[0],False))
            
            max_page=math.ceil(count/page_size)
            
            page=min(page,max_page)
            
            def get_page(levels:list[gd.Level],page:int):
                lines:list[str]=[]
                start=(page-1)*page_size
                
                levels1=levels[start:min(start+page_size,count)]
                
                l=lists[0]
                lines.append(f"{page}/{math.ceil(count/page_size)}页 ({start+1}-{min(start+page_size,count)} of {count})")
                lines.append(f"-gdlist -p <页数> <ListID> 以翻页.")
                
                for i in range(levels1.__len__()):
                    l=levels1[i]
                    lines.append(f"{i+start:>2} "+repr_level(l))
                return lines
            
            
            # 用转发消息打包
            if(bbot_api.can_pack_message(bot)):
                reply=await bbot_api.pack_message(bot,"\n".join(lines))
                assert reply
                
                for i in range(0,max_page):
                    lines2=get_page(levels,i+1)
                    reply2=await bbot_api.pack_message(bot,"\n".join(lines2))
                    if reply2:
                        reply+=reply2
                        
                await gdlist.finish(reply)
                    
            lines.extend(get_page(levels,page))
                
            await gdlist.finish("\n".join(lines))
            
        else:   
            lists,pageinfo=getList2(search,page-1,searchType=searchType)
            
            if not pageinfo.success():
                lines.append("查找出错.")
            elif lists.__len__()==0:
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
            
    except Exception as e:
        if isinstance(e,FinishedException):
            raise e
        await gdlist.finish("查询出错.")
        logger.error(traceback.format_exc())
    

gdthumb = on_command("gdthumb")
@gdthumb.handle()
async def _(bot:OBBot|DCBot,event:Event,args: Message = CommandArg()):
    raw_args=args.extract_plain_text().split()
    try:
        parser=ArgParser("gdthumb")
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
    
    await bbot_api.trigger_typing(bot,event)
    
    levels,pageinfo=getLevel2(search,page-1,rated)
    if not isinstance(levels,list) or not pageinfo.success():
        await gdthumb.finish("查找出错."+pageinfo.status.value)
        return
    if levels.__len__()==0:
        await gdthumb.finish("没有查找到任何关卡.")
        return
    elif levels.__len__()>1:
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
    
def buildMessageImage(bot:Bot,message:str,image:bytes,image_name:str):
    if isinstance(bot,OBBot):
        return(OBMessageSegment.text(message)+OBMessageSegment.image(image))
    else:
        return(DCMessage().append(message).append(DCMessageSegment.attachment(image_name,content=image)))

def get_help(bot:Bot,event:Event):
    if isinstance(bot,OBBot) or isinstance(bot,DCBot):
        return ["gdthumb [关名/ID] 获取关卡截图"]
    else:
        return []
    
def repr_level(l:gd.Level,fromuser:bool=False):
    return f"{l.name} by {l.creator} ({l.repr_difficulty()}) ({l.id})" if not fromuser else f"{l.name} ({l.repr_difficulty()}) ({l.id})"

def repr_list(l:gd.LevelList,fromuser:bool=False):
    return f"{l.name} by {l.creator} ({l.id}) ({l.levels.__len__()} 个关卡)" if not fromuser else f"{l.name} ({l.id}) ({l.levels.__len__()} 个关卡)"
