import os
from pathlib import Path
import time
import traceback
from typing import Any, TypeVar
from nonebot.adapters import Event,Bot,Message
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
from nonebot import get_driver,on_command,logger
from nonebot.permission import SUPERUSER
from .orb_storage import OrbStorage
from threading import Timer

driver=get_driver()

ORB_STORAGE=OrbStorage("config/orb_data.json")

def save_sync():
    ORB_STORAGE.save()
    logger.info(f"Saved {len(ORB_STORAGE.balances.keys())} entries.")
    
TIMER_THREAD=Timer(interval=300,function=save_sync)

@driver.on_startup
async def load_sessions():
    os.makedirs("config",exist_ok=True)
    ORB_STORAGE.load()
    logger.info(f"Loaded {len(ORB_STORAGE.balances.keys())} entries.")
    
    TIMER_THREAD.start()
    
@driver.on_shutdown
async def save_sessions():
    TIMER_THREAD.cancel()
    save_sync()

def get_orb_owner_id(event:Event):
    try:
        return event.get_user_id().replace(" ","_")
    except:
        return None
    
    
def add_balance(user:str,count:int,allow_negative:bool=False):
    return ORB_STORAGE.add_balance(user,count,allow_negative)

def get_balance(user:str):
    return ORB_STORAGE.get_balance(user)

orb_get=on_command("orb-get")
@orb_get.handle()
async def _(bot:Bot,event:Event, args: Message = CommandArg()):
    cmd_args=args.extract_plain_text().split()
    event_userid = get_orb_owner_id(event)
    
    is_superuser = await SUPERUSER(bot,event)
    
    try:
        if cmd_args.__len__()>=1:
            userid = cmd_args[0]
        else:
            if not event_userid:
                return
            userid = event_userid
            
        if not is_superuser and userid!=event_userid:
            await orb_get.finish("你没有权限查看别人的 Orbs.")
            
        if event_userid==userid:
            await orb_get.finish(f"你当前拥有 {get_balance(userid)} Orbs.")
        else:
            await orb_get.finish(f"{userid} 当前拥有 {get_balance(userid)} Orbs.")
        
    except Exception as e:
        if isinstance(e,FinishedException):
            raise e
        await orb_get.finish(f"错误: {e}")
        logger.error(f"Error: {traceback.format_exc()}")

orb_add=on_command("orb-add",permission=SUPERUSER)
@orb_add.handle()
async def _(bot:Bot,event:Event, args: Message = CommandArg()):
    cmd_args=args.extract_plain_text().split()
    userid = get_orb_owner_id(event)
    
    if(cmd_args.__len__()<2):
        await orb_add.finish(f"用法: orb-add 用户ID 数量\n你的用户ID:{userid}")
    try:
        userid = cmd_args[0]
        count = int(cmd_args[1])
        reply=[]
        
        result = add_balance(userid,count,False)
        if result:
            reply.append(f"已{'添加' if count>=0 else '扣除'} {abs(count)} Orbs. {userid} 现在拥有 {get_balance(userid)} Orbs.")
        else:
            reply.append(f"Orbs不足以扣除! {userid} 拥有 {get_balance(userid)} Orbs.")
            
        await orb_add.finish("\n".join(reply))
        
    except Exception as e:
        if isinstance(e,FinishedException):
            raise e
        await orb_add.finish(f"错误: {e}")
        logger.error(f"Error: {traceback.format_exc()}")