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

from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
require("bbot_api")
from ..bbot_api import get_user_id
from ..bbot_api.profile_link.events import on_link, LinkUserEvent, UnlinkUserEvent

driver=get_driver()

ORB_STORAGE=OrbStorage("config/orb_data.json")

def save_sync():
    if ORB_STORAGE.needs_save:
        ORB_STORAGE.save()
        logger.info(f"Saved {len(ORB_STORAGE.balances.keys())} entries.")

@driver.on_startup
async def load_sessions():
    os.makedirs("config",exist_ok=True)
    ORB_STORAGE.load()
    logger.info(f"Loaded {len(ORB_STORAGE.balances.keys())} entries.")
    scheduler.add_job(save_sync, "interval", seconds=10, id="ORBS_SAVE") 
    
@driver.on_shutdown
async def save_sessions():
    save_sync()

# ── profile_link 事件监听器 ──────────────────────────

@on_link(LinkUserEvent)
def _orb_on_link(event: LinkUserEvent):
    from ..bbot_api.profile_link.profile_link import get_profile_link_manager
    manager = get_profile_link_manager()
    if manager.migrate_dict(ORB_STORAGE.balances, event.raw_id, event.profile_id):
        logger.info(f"orb: 已迁移余额 {event.raw_id} → {event.profile_id}")

@on_link(UnlinkUserEvent)
def _orb_on_unlink(event: UnlinkUserEvent):
    from ..bbot_api.profile_link.profile_link import get_profile_link_manager
    manager = get_profile_link_manager()
    if manager.migrate_dict(ORB_STORAGE.balances, event.profile_id, event.raw_id):
        logger.info(f"orb: 已回迁余额 {event.profile_id} → {event.raw_id}")

def get_orb_owner_id(event:Event):
    """从事件中提取带平台前缀的用户 ID。"""
    try:
        return get_user_id(event)
    except:
        return None
    
    
def add_balance(user:str,count:int,allow_negative:bool=False):
    return ORB_STORAGE.add_balance(user,count,allow_negative)

def get_balance(user:str):
    return ORB_STORAGE.get_balance(user)

def user_exists(user:str):
    return ORB_STORAGE.balances.__contains__(user)

class OrbAccount:
    def __init__(self,user:str) -> None:
        self.user=user
    def add(self,count:int,allow_negative:bool=False):
        return add_balance(self.user,count,allow_negative)
    def get(self):
        return get_balance(self.user)
    
    @classmethod
    def fromEvent(cls,event:Event):
        userid=get_orb_owner_id(event)
        if userid:
            return cls(userid)
        else:
            return None
        
orb_id=on_command("orb-id")
@orb_id.handle()
async def _(bot:Bot,event:Event, args: Message = CommandArg()):
    event_userid = get_orb_owner_id(event)
    if event_userid:
        # Add 0 orbs to ensure account exists
        add_balance(event_userid,0,False)
    await orb_id.finish(f"你的orb id: {event_userid}")
    

orb_get=on_command("orb-get",aliases=set(["orb-get","orb-check"]))
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
        
        
orb_transfer=on_command("orb-transfer")
@orb_transfer.handle()
async def _(bot:Bot,event:Event, args: Message = CommandArg()):
    cmd_args=args.extract_plain_text().split()
    userid = get_orb_owner_id(event)
    if not userid:
        await orb_transfer.finish(f"内部错误: 找不到你的ID.")
    
    if(cmd_args.__len__()<2):
        await orb_transfer.finish(f"用法: orb-transfer 用户ID 数量\n你的用户ID:{userid}")
    try:
        target_id = cmd_args[0]
        count = int(cmd_args[1])
        reply=[]
        if count<0:
            await orb_transfer.finish("别想抢走别人的 Orbs!")
        elif count==0:
            await orb_transfer.finish("这有什么用呢?")
            
        if not user_exists(userid):
            await orb_transfer.finish("目标用户不存在, 请确认ID正确.")
        
        balance = get_balance(userid)
        
        if balance<count:
            await orb_transfer.finish(f"你的 Orbs 不足, 你只有 {balance} Orbs.")
        
        result = add_balance(userid,-count,False)
        result = add_balance(target_id,count,False)
        
        if result:
            reply.append(f"已转移 {count} Orbs. 你现在拥有{get_balance(userid)} Orbs.")
            reply.append(f"{target_id} 现在拥有 {get_balance(target_id)} Orbs.")
            
        await orb_transfer.finish("\n".join(reply))
        
    except Exception as e:
        if isinstance(e,FinishedException):
            raise e
        await orb_add.finish(f"错误: {e}")
        logger.error(f"Error: {traceback.format_exc()}")
        

def get_help(bot:Bot,event:Event):
    help_lines=[
            "orb-get 查看你持有的 Orbs"
            ]
    return help_lines