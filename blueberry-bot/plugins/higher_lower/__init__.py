
from enum import Enum
from nonebot import on_command,logger,get_plugin_config, require
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot import get_driver
from nonebot.matcher import Matcher

from .logic import GuessAction,GuessArgs,GuessSource
from .session import HigherLowerSession,SessionManager
from .models import HigherLowerLevel

require("bbot_api")
from ..bbot_api import getid,TextImageMessage,group_config
from ..bbot_api.profile_link.events import on_link, LinkUserEvent, UnlinkUserEvent
from ..bbot_api.argparse import ArgParser
from .. import bbot_api
require("gd_api")
from ..gd_api.pemonlist import getPemonlistLevels_async, Level as PemonlistLevel
from ..gd_api.aredl import getAREDLLevels_async, Level as AREDLLevel
from ..gd_api import thumbs
from ..gd_api import gd

try:
    require("orb_api")
    from .. import orb_api
except:
    orb_api=None
    
SESSION_MANAGER:SessionManager=SessionManager()
    
higher_lower=on_command("gdhol")
@higher_lower.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    text=msg.extract_plain_text()
    
    event_id=getid(event)
    args=GuessArgs(text)
    
    reply=TextImageMessage.build(bot)
    
    session = SESSION_MANAGER.get_or_create(event_id)
    
    if args.action == GuessAction.START:
        provider = args.getProvider()
        if not provider:
            return
        levels = await provider.getLevels("")
        if not session.finished:
            reply.addLine("当前有正在进行的猜测, 请继续猜测")
            await reply.finish(higher_lower)
        session.start(levels)
        
        await formatLevelsToReply(reply,session)
        reply.addLine("这一关的排名比上一关高还是低呢? 请输入 -gdhol >或< 以回答")
        await reply.finish(higher_lower)
        
    elif args.action == GuessAction.GUESS:
        if session.finished:
            reply.addLine("当前没有正在进行的猜测, 请重新开始")
            await reply.finish(higher_lower)
        
        HIGH_KEYWORD=["high","higher","高",">"]
        LOW_KEYWORD=["low","lower","低","<"]
        comp=0
        if args.text in HIGH_KEYWORD:
            comp=1
        elif args.text in LOW_KEYWORD:
            comp=-1
            
        if comp==0:
            reply.addLine(f"请输入 {','.join(HIGH_KEYWORD)} 或 {','.join(LOW_KEYWORD)} 以猜测!")
            await reply.finish(higher_lower)
            
        guess_result=session.do_guess(comp)
        if guess_result:
            reply.addLine("回答正确!")
            
            session.choice()
            await formatLevelsToReply(reply,session)
            reply.addLine("这一关的排名比上一关高还是低呢? 请输入 -gdhol >或< 以回答")
        else:
            session.finished=True
            reply.addLine("回答错误!")
            levels=session.getLastLevels()
            if levels:
                l1,l2=levels
                reply.addLine(formatLevel(l1,True))
                reply.addLine(formatLevel(l2,True))
                
        await reply.finish(higher_lower)
        
    elif args.action == GuessAction.GIVEUP:
        if session.finished:
            reply.addLine("当前没有正在进行的猜测, 请重新开始")
            await reply.finish(higher_lower)
            
        reply.addLine("你放弃了!")
        session.finished=True
        levels=session.getLastLevels()
        if levels:
            l1,l2=levels
            reply.addLine(formatLevel(l1,True))
            reply.addLine(formatLevel(l2,True))
        await reply.finish(higher_lower)
        
        
            
            
async def formatLevelsToReply(reply:TextImageMessage,session:HigherLowerSession):
    levels=session.getLastLevels()
    if levels:
        l1,l2 = levels
        await addThumb(reply,l1.get_id())
        reply.addLine(formatLevel(l1,True))
        reply.addLine("")
        await addThumb(reply,l2.get_id())
        reply.addLine(formatLevel(l2))
        
def formatLevel(level:HigherLowerLevel,placement:bool=False):
    return f"{level.get_repr()} #{level.get_placement() if placement else '?'}"

async def addThumb(msg:TextImageMessage,id:int):
    thumb=await thumbs.getThumbnail_async(id,small=True)
    if thumb:
        msg.addImage(thumb)