import os
import random
import re
import traceback
from typing import Any, TypeVar
import cv2
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment,GuildMessageCreateEvent
from nonebot.params import CommandArg
import nonebot.config
from nonebot import get_driver
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from pathlib import Path

from .guess_utils import get_variance_cv2,random_crop,isnonsense_cv2
from .config import Config
from . import gd_api,thumbnail_api
from .guess_session import GuessSession,SessionManager

plugin_config = get_plugin_config(Config)

DATA_PATH=Path()/"gdguess_data"
SAVE_PATH=DATA_PATH/"sessions.json"

session_manager:SessionManager=SessionManager()

driver=get_driver()

@driver.on_startup
async def load_sessions():
    os.makedirs(DATA_PATH,exist_ok=True)
    session_manager.load(SAVE_PATH.as_posix())
    logger.info(f"Loaded {len(session_manager.sessions)} sessions.")
    
@driver.on_shutdown
async def save_sessions():
    session_manager.save(SAVE_PATH.as_posix())
    logger.info(f"Saved {len(session_manager.sessions)} sessions.")

gdguess_start = on_command("gdguess_start")
@gdguess_start.handle()
async def _(event:Event,args: Message = CommandArg()):
    await guess_start(gdguess_start,event,args,test=False)
    await gdguess_start.finish()
    
gdguess_hard = on_command("gdguess_hard")
@gdguess_hard.handle()
async def _(event:Event,args: Message = CommandArg()):
    await guess_start(gdguess_hard,event,args,crop_size=(128,128),test=False)
    await gdguess_hard.finish()
    
gdguess_insane = on_command("gdguess_insane")
@gdguess_insane.handle()
async def _(event:Event,args: Message = CommandArg()):
    await guess_start(gdguess_insane,event,args,crop_size=(64,64),test=False)
    await gdguess_insane.finish()
    
gdguess_extreme = on_command("gdguess_extreme")
@gdguess_extreme.handle()
async def _(event:Event,args: Message = CommandArg()):
    await guess_start(gdguess_extreme,event,args,crop_size=(32,32),test=False)
    await gdguess_extreme.finish()
    
gdguess_test = on_command("gdguess_test",permission=SUPERUSER)
@gdguess_test.handle()
async def _(event:Event,args: Message = CommandArg()):
    await guess_start(gdguess_test,event,args,test=True)
    await gdguess_test.finish()

async def guess_start(matcher:type[Matcher],event:Event,args: Message = CommandArg(),crop_size:tuple[int,int]=(256,256),test:bool=False):
    args_text=[i.strip() for i in args.extract_plain_text().split(",")]
    
    id=getid(event)
    session=session_manager.sessions.get(id)
    if session and not session.completed:
        await matcher.send("你已经有一个正在进行的游戏了! 继续猜图吧!")
        
        
    msg=[]
    levels:list[int]=[]
    
    empty_search=not args_text or args_text==[""]
    
    if empty_search and session and session.completed:
        levels.extend(session.level_pool)
        msg.append("继续使用上次的关卡池进行游戏!")
    elif empty_search:
        await matcher.send("请输入至少一个List ID! 多个ID请用,分隔")
        return
    else:
        # Get levels from the provided lists
        for i in args_text:
            lists=gd_api.getList(i)
            if lists.__len__()>1:
                msg.append(f"关键词 {i} 查找到多个List. 请输入List ID选择具体的List.")
                for l in lists:
                    msg.append(f"{l.id} = {l.name} by {l.creator}")
                await matcher.send("\n".join(msg))
                return
            
            levels.extend(lists[0].levels)
        
    
    image_path=DATA_PATH/"images"
    os.makedirs(image_path,exist_ok=True)
    # Choose a random level
    levelID,img=roll_until_level(levels)
    # Chosen level
    level=gd_api.getLevel(levelID)[0]
    
    cachepath=image_path/f"{id}.webp"
    with open(cachepath,"wb") as f:
        f.write(img)
    
    if test:
        msg.append(f"[TEST] {level.name} by {level.creator}, {level.id}")
        await matcher.send(DCMessage().append("\n".join(msg)).append(MessageSegment.attachment("guess.png",content=img)))
    else:
        crop_width, crop_height = crop_size
        cropped_path = image_path/f"{id}.png"
        
        image = cv2.imread(cachepath)
        
        assert image is not None
        
        left, top, right, bottom, cropped_image = random_crop(crop_width, crop_height, image)
        for i in range(0,20):
            left, top, right, bottom, cropped_image = random_crop(crop_width, crop_height, image)
            if (not isnonsense_cv2(cropped_image)): break
        cv2.imwrite(cropped_path,cropped_image)
        
        session_manager.sessions[id]=GuessSession.start(id,level,crop=(left, top, right, bottom),level_pool=levels)
        
        msg.append("以下截图是来自哪个关卡呢? 输入 -guess 你的答案 以回答")
        await matcher.send(DCMessage().append("\n".join(msg)).append(MessageSegment.attachment("guess.png",content=loadFile(cropped_path))))
    
    

gdguess = on_command("gdguess")
@gdguess.handle()
async def _(event:Event,args: Message = CommandArg()):
    id=getid(event)
    session=session_manager.sessions.get(id)
    if not session or session.completed:
        await gdguess.send("你还没有正在进行的猜图游戏! 输入 -gdguess_start [List ID] 来开始一个新的游戏.")
        return
    guess=args.extract_plain_text().strip()
    if session.guess(guess):
        session.completed=True
        msg=f"恭喜你猜对了! 关卡是 {session.level_name} by {session.level_creator}, 你总共猜了 {session.guesses} 次!"
        await gdguess.send(DCMessage().append(msg).append(MessageSegment.attachment("answer.png",content=guess_utils.draw_rectangle_on_image(DATA_PATH/"images"/f"{id}.webp",session.crop))))
    else:
        await gdguess.send(f"猜错了! 这是 {session.guesses} 次猜测了, 继续加油!")
    await gdguess.finish()
    
gdguess_giveup = on_command("gdguess_giveup")
@gdguess_giveup.handle()
async def _(event:Event):
    id=getid(event)
    session=session_manager.sessions.get(id)
    if not session or session.completed:
        await gdguess_giveup.send("你还没有正在进行的猜图游戏! 输入 -gdguess_start [List ID] 来开始一个新的游戏.")
        return
    session.completed=True
    
    msg=f"游戏结束! 关卡是 {session.level_name} by {session.level_creator}, 你总共猜了 {session.guesses} 次!"
    await gdguess.send(DCMessage().append(msg).append(MessageSegment.attachment("answer.png",content=guess_utils.draw_rectangle_on_image(DATA_PATH/"images"/f"{id}.webp",session.crop))))
    await gdguess_giveup.finish()

def roll_until_level(levels:list[int]):
    levels2=levels.copy()
    img=None
    while not img:
        levelID = random.choice(levels2)
        img=thumbnail_api.getThumbnail(levelID,plugin_config.level_thumbnails_api_base)
        if not img:
            levels2.remove(levelID)
            
    return levelID,img



def getid(event: Event) -> str:
    if isinstance(event,GuildMessageCreateEvent):
        return "dc"+str(event.guild_id)
    else:
        return "u" + str(event.get_user_id())
    
def loadFile(file:str|Path) -> bytes:
    with open(file,'rb') as f:
        return f.read()