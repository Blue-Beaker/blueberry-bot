from enum import Enum
import os
import random
import time
from typing import Optional
import cv2
from nonebot import on_command,logger,get_plugin_config, require
from nonebot.adapters import Message,Event,Bot
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment

from nonebot.params import CommandArg
from nonebot import get_driver
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from pathlib import Path

from numpy import ndarray
import requests

from .guess_utils import random_crop,isnonsense_cv2
from .config import Config
from . import gd_api,thumbnail_api
from .guess_session import GuessSession,SessionManager,ConfigManager,ConfigEntry
from .pemonlist import getPemonlistLevels

require("bbot_api")
from ..bbot_api import getid,reaction_emoji,loadFile

plugin_config = get_plugin_config(Config)

DATA_PATH=Path()/"gdguess_data"
SAVE_PATH=DATA_PATH/"sessions.json"
CONFIG_PATH=DATA_PATH/"config.json"
IMAGES_PATH=DATA_PATH/"images"

session_manager:SessionManager=SessionManager(SAVE_PATH.as_posix())
config_manager:ConfigManager=ConfigManager(CONFIG_PATH.as_posix())
next_guess_time:dict[str,int]={}
last_finish_time:dict[str,int]={}

driver=get_driver()

@driver.on_startup
async def load_sessions():
    os.makedirs(DATA_PATH,exist_ok=True)
    session_manager.load()
    config_manager.load()
    logger.info(f"Loaded {len(session_manager.entries)} sessions.")
    
@driver.on_shutdown
async def save_sessions():
    session_manager.save()
    config_manager.save()
    logger.info(f"Saved {len(session_manager.entries)} sessions.")
    SAVE_MANAGER.clean()

class SaveManager:
    next_save_time:int=0
    def autosave(self):
        if time.time()>self.next_save_time:
            self.save()
            self.next_save_time=int(time.time())+plugin_config.gdguess_save_interval
            
    def save(self):
        session_manager.save()
        config_manager.save()
        logger.info(f"Saved {len(session_manager.entries)} sessions.")
        
    def clean(self):
        files_to_delete:list[Path]=[]
        for f in os.listdir(IMAGES_PATH):
            if f.endswith(".png") or f.endswith(".webp"):
                if f.removesuffix(".png").removesuffix(".webp") not in session_manager.entries.keys():
                    files_to_delete.append(IMAGES_PATH/f)
        for f in files_to_delete:
            os.remove(f)
        
SAVE_MANAGER=SaveManager()
            
    
gdguess_test = on_command("gdguess-test",permission=SUPERUSER)
@gdguess_test.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    await guess_start(bot,gdguess_test,event,GuessArgs(args.extract_plain_text()),test=True)
    await gdguess_test.finish()

class GuessAction(Enum):
    GUESS="guess"
    START="start"
    GIVEUP="giveup"
    HELP="help"
    HINT="hint"
class GuessSource(Enum):
    LAST="last"
    LIST="list"
    PEMONLIST="pemonlist"
class Difficulty(Enum):
    EASY=("easy",(512,512))
    HARD=("hard",(256,256))
    INSANE=("insane",(128,128))
    EXTREME=("extreme",(64,64))
    
    
class GuessArgs:
    action:GuessAction
    source:GuessSource
    difficulty:Difficulty
    def __init__(self,text:str) -> None:
        self.action=GuessAction.GUESS
        self.source=GuessSource.LIST
        self.difficulty=Difficulty.EASY
        
        args=text.split(" ")
        while args and args[0].startswith("-"):
            arg=args[0].removeprefix("-")
            args.pop(0)
            self.applyArg(arg)
            
        self.text=" ".join(args)
        
        if self.source==GuessSource.LIST and self.text.strip()=="":
            self.source=GuessSource.LAST
            
    def applyArg(self,arg:str):
            for i in GuessAction:
                if arg==i.value:
                    self.action=i
                    return
            for i in GuessSource:
                if arg==i.value:
                    self.source=i
                    return
            for i in Difficulty:
                if arg==i.value[0]:
                    self.difficulty=i
                    self.action=GuessAction.START
                    return
            
        
def get_levels_from_args(args:GuessArgs,session:Optional[GuessSession]):
    levels:list[int]=[]
    if args.source==GuessSource.PEMONLIST:
        pemonlist_levels=getPemonlistLevels()
        if not pemonlist_levels:
            return None,"无法获取Pemonlist的关卡数据."
        levels.extend([l.level_id for l in pemonlist_levels])
        return levels,"关卡池已设置为Pemonlist的关卡!"
    elif args.source==GuessSource.LAST and session:
        levels.extend(session.level_pool)
        return levels,"继续使用上次的关卡池进行游戏!"
    else:
        args_text=[i.strip() for i in args.text.split(",")]
        if not args_text or args_text==[""]:
            return None,"请输入至少一个List ID! 多个ID请用,分隔"
        # Get levels from the provided lists
        for i in args_text:
            if not i:
                continue
            lists=gd_api.getList(i)
            if lists.__len__()==0:
                return None,f"关键词 {i} 没有查找到任何List."
            if lists.__len__()>1:
                lines=[f"关键词 {i} 查找到多个List. 请输入List ID选择具体的List."]
                for l in lists:
                    lines.append(f"{l.id} = {l.name} by {l.creator}")
                return None,"\n".join(lines)
            
            levels.extend(lists[0].levels)
        if levels.__len__()==0:
            return None,"在你提供的List中没有找到任何关卡."
        return levels,"关卡池已设置为你提供的List中的关卡!"
    return levels,None
    
gdguess = on_command("gdguess")
@gdguess.handle()
async def _(bot:Bot,event:Event,raw_args: Message = CommandArg()):
    # Only allow in Certain Adapters
    if not isSupportedAdapter(bot):
        return
    
    args_text=raw_args.extract_plain_text().strip()
    
    args=GuessArgs(args_text)
    args_text=args.text
    if args.action == GuessAction.HELP:
        help=[
        "gdguess -start [list IDs] 开始猜GD关卡",
        "使用list ID指定关卡池, 多个list用,分割",
        "也可加入-pemonlist参数使用Pemonlist作为关卡池",
        "将-start替换为-hard,-insane或-extreme可开始更高难度(截取范围更小)的猜图",
        "不输入list或使用-last参数则沿用上次的关卡池",
        "举例: '-gdguess -insane 83317' 使用该list开始insane难度的猜图",
        "gdguess -help 显示详细帮助",
        "gdguess -hint 获取提示",
        "gdguess -giveup 放弃当前的猜图游戏并显示答案",
        "gdguess <图名> 进行猜图",]
        await gdguess.send("\n".join(help))
        await gdguess.finish()
        return
    
    id=getid(event)
    session=session_manager.entries.get(id)
    if session and not session.completed:
        recover_cache_img(id,session)
    
    if args.action == GuessAction.GIVEUP:
        await giveup(bot,gdguess,event)
        await gdguess.finish()
        return
    
    elif args.action == GuessAction.START:
        await guess_start(bot,gdguess,event,args,crop_size=args.difficulty.value[1],test=False)
        await gdguess.finish()
        return
    
    elif args.action == GuessAction.HINT:
        await hint(bot,gdguess,event)
        await gdguess.finish()
        return
    
    id=getid(event)
    session=session_manager.entries.get(id)
    if not session or session.completed:
        msg="你还没有正在进行的猜图游戏! 输入 -gdguess -start [List ID] 来开始一个新的游戏.\n-start换成 -hard/-insane/-extreme 可以获得更小的截图, 但难度也会更大哦!"
        
        if isinstance(bot,OBBot) and isinstance(event,OBGroupMessageEvent):
            await reaction_emoji(bot,event.message_id,10068) # Questionmark
        # Dont send tips when it's just finished
        if time.time()-last_finish_time.get(id,0)>10:
            await gdguess.send(msg)
        
        await gdguess.finish()
        return
    guess=raw_args.extract_plain_text().strip()
    if session.guess(guess):
        session.completed=True
        msg=f"恭喜你猜对了! 关卡是 {session.level_name} by {session.level_creator}, 你总共猜了 {session.guesses} 次!"
        if session.hints_used:
            msg=msg+" (已使用提示)"
        
        await gdguess.send(buildMessageImage(bot,msg,guess_utils.draw_rectangle_on_image(DATA_PATH/"images"/f"{session.session_id}.webp",session.crop)),at_sender=True)
        if isinstance(bot,OBBot) and isinstance(event,OBGroupMessageEvent):
            await reaction_emoji(bot,event.message_id,144) # Confetti emoji
            
        last_finish_time[id]=int(time.time())
        
        removeImages(id)
    else:
        if isinstance(bot,OBBot) and isinstance(event,OBGroupMessageEvent):
            await reaction_emoji(bot,event.message_id,424) # Button emoji
        if session.guesses%5==0:
            await sendMessageAndImage(bot,gdguess,f"猜错了! 这是 {session.guesses} 次猜测了, 继续加油!\n需要提示吗? -gdguess -hint 以获取提示",loadFile(IMAGES_PATH/f"{id}.png"))
        elif not isinstance(bot,OBBot):
            await gdguess.send(f"猜错了! 这是 {session.guesses} 次猜测了, 继续加油!")
        
    SAVE_MANAGER.autosave()
    await gdguess.finish()
    

async def guess_start(bot:Bot,matcher:type[Matcher],event:Event,args:GuessArgs,crop_size:tuple[int,int]=(256,256),test:bool=False):
    # Only allow in Certain Adapters
    if not isSupportedAdapter(bot):
        return
    # text=args.text
    # args_text=[i.strip() for i in text.split(",")]
    
    id=getid(event)
    session=session_manager.entries.get(id)
    
    # When session is active
    if session and not session.completed:
        await sendMessageAndImage(bot,gdguess,f"你已经有一个正在进行的游戏了! 继续猜图吧!",loadFile(IMAGES_PATH/f"{session.session_id}.png"))
        return
    
    # When on cooldown
    cooldown=next_guess_time.get(id,0)-int(time.time())
    if cooldown>0:
        if isinstance(bot,OBBot) and isinstance(event,OBGroupMessageEvent):
            await reaction_emoji(bot,event.message_id,424) # Button emoji
        else:
            await matcher.send(f"再过{id}秒才能再次开始哦")
        return
    # Find levels
    lines=[]
    
    levels,msg=get_levels_from_args(args,session)
    
    if msg:
        lines.append(msg)
    if not levels:
        await matcher.send("\n".join(lines))
        return
    
    # Set cooldown
    if not test:
        next_guess_time[id]=int(time.time())+config_manager.get_or_create(id,get_default_config(id)).cooldown
    # Actually start the guess
        
    os.makedirs(IMAGES_PATH,exist_ok=True)
    
    # Choose a random level
    levelID=None
    img=None
    try:
        levelID,img=roll_until_level(levels)
    except requests.ConnectionError as e:
        logger.error(f"Error fetching level thumbnail: {e}")
        await matcher.send("获取关卡截图时发生错误.")
        return
    if not levelID or not img:
        await matcher.send("错误:未找到有截图的关卡.")
        return
        
    # Chosen level
    fetched_levels=gd_api.getLevel(levelID)
    
    if not fetched_levels:
        await matcher.send("错误:未找到关卡信息")
        return
    
    level=fetched_levels[0]
    
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
        
        session=session_manager.get_or_create(id)
        session.start(id,level,crop=(left, top, right, bottom),level_pool=levels)
        # session_manager.entries[id]=session
        
        lines.append("以下截图是来自哪个关卡呢? 输入 -gdguess 你的答案 以回答")
        msg="\n".join(lines)
        await sendMessageAndImage(bot,matcher,msg,loadFile(cropped_path))
        
        SAVE_MANAGER.autosave()
        await matcher.finish()
    
async def hint(bot:Bot,matcher:type[Matcher],event:Event):
    id=getid(event)
    session=session_manager.entries.get(id)
    if not session or session.completed:
        await matcher.send("你还没有正在进行的猜图游戏! 输入 -gdguess_start [List ID] 来开始一个新的游戏.")
        return
    
    if not session.hints_used:
        hint_text = []
        charactors = []
        for i in range(len(session.level_name)):
            c=session.level_name[i]
            if c not in " -":
                charactors.append(i)
                hint_text.append("_")
            else:
                hint_text.append(c)
                
        for i in random.choices(charactors,k=int((len(charactors)-1)/3)):
            hint_text[i]=session.level_name[i]
        
        session.hint_text=" ".join(hint_text)
        session.hints_used=1
        
    await matcher.send(f"提示: {session.hint_text}")
    return
    
    
   
async def giveup(bot:Bot,matcher:type[Matcher],event:Event):
    id=getid(event)
    session=session_manager.entries.get(id)
    if not session or session.completed:
        await matcher.send("你还没有正在进行的猜图游戏! 输入 -gdguess_start [List ID] 来开始一个新的游戏.")
        return
    session.completed=True
    
    msg=f"游戏结束! 关卡是 {session.level_name} by {session.level_creator}, 你总共猜了 {session.guesses} 次!"
    await sendMessageAndImage(bot,matcher,msg,guess_utils.draw_rectangle_on_image(DATA_PATH/"images"/f"{id}.webp",session.crop),"answer.png")
    removeImages(id)
    SAVE_MANAGER.autosave()

gdguess_config = on_command("gdguess-config",permission=SUPERUSER)
@gdguess_config.handle()
async def _(bot:Bot,event:Event,raw_args: Message = CommandArg()):
    id=getid(event)
    
    args:dict[str,str|int|bool]={}
    for seg in raw_args.extract_plain_text().split(","):
        spl=seg.split("=",1)
        if spl.__len__()==2:
            args[spl[0]]=spl[1]
            
    modified=False
    cfg=config_manager.get_or_create(id,get_default_config(id))
    try:
        new_cd=args.get("cooldown",None)
        if new_cd:
            cfg.cooldown=int(new_cd)
            modified=True
    except:
        pass
    
    config_manager.save()
    
    if modified:
        await gdguess_config.finish(f"已更新本会话的guess配置:\n{cfg.__str__()}")
    else:
        await gdguess_config.finish(f"本会话的guess配置未改变:\n{cfg.__str__()}")
 
def roll_until_level(levels:list[int]):
    levels2=levels.copy()
    img=None
    levelID=None
    while levels2 and not img:
        levelID = random.choice(levels2)
        img=thumbnail_api.getThumbnail(levelID,plugin_config.level_thumbnails_api_base)
        if not img:
            levels2.remove(levelID)
            
    return levelID,img

def recover_cache_img(id:str,session:GuessSession):
    cachepath=IMAGES_PATH/f"{id}.webp"
    cropped_path = IMAGES_PATH/f"{id}.png"
    
    # Fetch thumbnail
    if not os.path.exists(cachepath):
        logger.error(f"Recovering thumbnail for {id}")
        try:
            rawimg=thumbnail_api.getThumbnail(session.level_id,plugin_config.level_thumbnails_api_base)
        except requests.ConnectionError as e:
            logger.error(f"Error fetching level thumbnail: {e}")
            return False
    
        if not rawimg:
            return False
        with open(cachepath,"wb") as f:
            f.write(rawimg)
            
    if not os.path.exists(cropped_path):
        logger.error(f"Recovering cropped image for {id}")
        img = cv2.imread(cachepath)
        if not isinstance(img,ndarray):
            return False
        cropped=guess_utils.crop_image(img,*session.crop)
        cv2.imwrite(cropped_path,cropped)
    return True

def isSupportedAdapter(bot:Bot):
    return isinstance(bot,DCBot) or isinstance(bot,OBBot)

async def sendMessageAndImage(bot:Bot,matcher:type[Matcher],message:str,image:bytes,image_name:str="guess.png"):
    await matcher.send(buildMessageImage(bot,message,image,image_name))
        
def buildMessageImage(bot:Bot,message:str,image:bytes,image_name:str="guess.png"):
    if isinstance(bot,OBBot):
        return(OBMessageSegment.text(message)+OBMessageSegment.image(image))
    else:
        return(DCMessage().append(message).append(DCMessageSegment.attachment(image_name,content=image)))

def get_default_config(id:str):
    if id.startswith("group"):
        return {"cooldown":60}
    else:
        return {"cooldown":10}
    
def removeImages(id:str):
    for ext in ["webp","png"]:
        path=IMAGES_PATH/f"{id}.{ext}"
        if path.exists():
            path.unlink()
    
def get_help(bot:Bot,event:Event):
    help_lines=[
        "gdguess 截图猜GD关卡",
        "gdguess -help 显示gdguess相关帮助"
    ]
    return help_lines