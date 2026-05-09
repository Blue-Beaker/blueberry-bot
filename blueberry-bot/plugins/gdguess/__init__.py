import os
import random
import re
import traceback
from typing import Any, TypeVar
import cv2
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment

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
IMAGES_PATH=DATA_PATH/"images"

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
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    await guess_start(bot,gdguess_start,event,args,test=False)
    await gdguess_start.finish()
    
gdguess_hard = on_command("gdguess_hard")
@gdguess_hard.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    await guess_start(bot,gdguess_hard,event,args,crop_size=(128,128),test=False)
    await gdguess_hard.finish()
    
gdguess_insane = on_command("gdguess_insane")
@gdguess_insane.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    await guess_start(bot,gdguess_insane,event,args,crop_size=(64,64),test=False)
    await gdguess_insane.finish()
    
gdguess_extreme = on_command("gdguess_extreme")
@gdguess_extreme.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    await guess_start(bot,gdguess_extreme,event,args,crop_size=(32,32),test=False)
    await gdguess_extreme.finish()
    
gdguess_test = on_command("gdguess_test",permission=SUPERUSER)
@gdguess_test.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    await guess_start(bot,gdguess_test,event,args,test=True)
    await gdguess_test.finish()

async def guess_start(bot:Bot,matcher:type[Matcher],event:Event,args: Message = CommandArg(),crop_size:tuple[int,int]=(256,256),test:bool=False):
    # Only allow in Certain Adapters
    if not isSupportedAdapter(bot):
        return
    args_text=[i.strip() for i in args.extract_plain_text().split(",")]
    
    id=getid(event)
    session=session_manager.sessions.get(id)
    if session and not session.completed:
        await matcher.send("你已经有一个正在进行的游戏了! 继续猜图吧!")
        
        
    lines=[]
    levels:list[int]=[]
    
    empty_search=not args_text or args_text==[""]
    
    if empty_search and session and session.completed:
        levels.extend(session.level_pool)
        lines.append("继续使用上次的关卡池进行游戏!")
    elif empty_search:
        await matcher.send("请输入至少一个List ID! 多个ID请用,分隔")
        return
    else:
        # Get levels from the provided lists
        for i in args_text:
            lists=gd_api.getList(i)
            if lists.__len__()>1:
                lines.append(f"关键词 {i} 查找到多个List. 请输入List ID选择具体的List.")
                for l in lists:
                    lines.append(f"{l.id} = {l.name} by {l.creator}")
                await matcher.send("\n".join(lines))
                return
            
            levels.extend(lists[0].levels)
        
    os.makedirs(IMAGES_PATH,exist_ok=True)
    # Choose a random level
    levelID,img=roll_until_level(levels)
    # Chosen level
    level=gd_api.getLevel(levelID)[0]
    
    cachepath=IMAGES_PATH/f"{id}.webp"
    with open(cachepath,"wb") as f:
        f.write(img)
    
    if test:
        lines.append(f"[TEST] {level.name} by {level.creator}, {level.id}")
        msg="\n".join(lines)
        await sendMessageAndImage(bot,matcher,msg,img)
        
    else:
        crop_width, crop_height = crop_size
        cropped_path = IMAGES_PATH/f"{id}.png"
        
        image = cv2.imread(cachepath)
        
        assert image is not None
        
        left, top, right, bottom, cropped_image = random_crop(crop_width, crop_height, image)
        for i in range(0,20):
            left, top, right, bottom, cropped_image = random_crop(crop_width, crop_height, image)
            if (not isnonsense_cv2(cropped_image)): break
        cv2.imwrite(cropped_path,cropped_image)
        
        session_manager.sessions[id]=GuessSession.start(id,level,crop=(left, top, right, bottom),level_pool=levels)
        
        lines.append("以下截图是来自哪个关卡呢? 输入 -gdguess 你的答案 以回答")
        msg="\n".join(lines)
        await sendMessageAndImage(bot,matcher,msg,loadFile(cropped_path))
    
    

gdguess = on_command("gdguess")
@gdguess.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    # Only allow in Certain Adapters
    if not isSupportedAdapter(bot):
        return
    
    id=getid(event)
    session=session_manager.sessions.get(id)
    if not session or session.completed:
        await gdguess.send("你还没有正在进行的猜图游戏! 输入 -gdguess_start [List ID] 来开始一个新的游戏.")
        return
    guess=args.extract_plain_text().strip()
    if session.guess(guess):
        session.completed=True
        msg=f"恭喜你猜对了! 关卡是 {session.level_name} by {session.level_creator}, 你总共猜了 {session.guesses} 次!"
        
        await sendMessageAndImage(bot,gdguess,msg,guess_utils.draw_rectangle_on_image(DATA_PATH/"images"/f"{id}.webp",session.crop))
        # await gdguess.send(DCMessage().append(msg).append(DCMessageSegment.attachment("answer.png",content=guess_utils.draw_rectangle_on_image(DATA_PATH/"images"/f"{id}.webp",session.crop))))
        removeImages(id)
    else:
        if isinstance(bot,OBBot):
            if random.randint(0,5)==0:
                await gdguess.send(f"猜错了! 这是 {session.guesses} 次猜测了, 继续加油!")
            return
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
    
    await gdguess.send(DCMessage().append(msg).append(DCMessageSegment.attachment("answer.png",content=guess_utils.draw_rectangle_on_image(DATA_PATH/"images"/f"{id}.webp",session.crop))))
    removeImages(id)
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

def isSupportedAdapter(bot:Bot):
    return isinstance(bot,DCBot) or isinstance(bot,OBBot)

async def sendMessageAndImage(bot:Bot,matcher:type[Matcher],message:str,image:bytes,image_name:str="guess.png"):
    if isinstance(bot,OBBot):
        await matcher.send(OBMessageSegment.text(message)+OBMessageSegment.image(image))
    else:
        await matcher.send(DCMessage().append(message).append(DCMessageSegment.attachment(image_name,content=image)))

def getid(event: Event) -> str:
    if isinstance(event,GuildMessageCreateEvent):
        return "dc"+str(event.guild_id)
    else:
        return "u" + str(event.get_user_id())
    
def loadFile(file:str|Path) -> bytes:
    with open(file,'rb') as f:
        return f.read()
    
def removeImages(id:str):
    for ext in ["webp","png"]:
        path=IMAGES_PATH/f"{id}.{ext}"
        if path.exists():
            path.unlink()