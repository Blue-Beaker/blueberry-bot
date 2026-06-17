

import json
import os
import random
from nonebot import logger, on_command, get_driver, require
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg

from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment
from nonebot.adapters.discord import MessageEvent as DCMessageEvent, MessageSegment as DCMessageSegment, Message as DCMessage

from ..bbot_api import getid

from . import guess_data
from . import handler_mc
from . import handler_dc
from . import handler_base
from .handler_base import INSTANCES,guess_command

try:
    require("orb_api")
    from .. import orb_api
except:
    orb_api=None

SESSIONS_FILE="guess_sessions.json"


driver=get_driver()

loadEntityCats=[]

@driver.on_startup
async def load():
    
    guess_data.load_all_data()
    for value in guess_data.ENTITY_MANAGER.category_data.values():
        loadEntityCats.append(f"{value.id}={value.name}")
        

    logger.info(f"已加载{len(loadEntityCats)}个实体类别, {len(guess_data.MAP_MANAGER.map_data.keys())}个地图")
    logger.debug(f"实体类别: {', '.join(loadEntityCats)}")
    logger.debug(f"地图: {', '.join(guess_data.MAP_MANAGER.map_data.keys())}")

    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE,"r") as f:
            handler_base.INSTANCES.load(json.load(f))
            logger.info(f"已加载{len(handler_base.INSTANCES.dump().keys())}个会话")
            logger.debug(f'会话: {handler_base.INSTANCES.dump()}')
        # 加载后立即以新格式覆写，完成自动迁移
        saveSessions()
@driver.on_shutdown
async def save_sessions():
    saveSessions()
    
    

        
def saveSessions():
    with open(SESSIONS_FILE,"w") as f:
        json.dump(handler_base.INSTANCES.dump(),f,ensure_ascii=False,indent=2)
        
handler_base.after_command=saveSessions

handler_msg = on_command("guess")
@handler_msg.handle()
async def _(bot:Bot,event:Event,args: Message = CommandArg()):
    manager=INSTANCES.getOrCreateGuessManager(getid(event))
    
    message=args.extract_plain_text().strip()
    logger.debug(f"'{message}' from{event}")
    feedBackMessage = guess_command(message,manager)
    
    if(feedBackMessage):
        
        if "你猜对了" in feedBackMessage:
            if orb_api:
                orb_id=orb_api.get_orb_owner_id(event)
                if orb_id:
                    add_orbs=random.randint(100,500)
                    orb_api.add_balance(orb_id,add_orbs)
                    feedBackMessage=feedBackMessage+f"\n你获得了 {add_orbs} Orbs"
                
        if isinstance(event,DCMessageEvent):
            split=feedBackMessage.split("{username}")
            msgseg=split[0]
            for segment in split[1:]:
                msgseg=msgseg+DCMessageSegment.mention_user(event.user_id)+DCMessageSegment.text(segment)
            await handler_msg.send(msgseg)
        elif isinstance(event,MCBaseChatEvent):
            await handler_msg.send(f"{feedBackMessage}".replace("{username}",event.player.nickname))
        elif isinstance(event,OBGroupMessageEvent):
            split=feedBackMessage.split("{username}")
            msgseg=OBMessageSegment.text(split[0])
            for segment in split[1:]:
                msgseg=msgseg+OBMessageSegment.at(event.user_id)+OBMessageSegment.text(segment)
            await handler_msg.send(msgseg)
        else:
            await handler_msg.send(feedBackMessage.replace("{username}",""))
        
    pass

def get_help(bot:Bot,event:Event)->str:
    help_lines=[
        "guess <start|giveup> 开始/放弃猜图 (题库为蔚蓝草莓酱)",
        "guess <图名> 进行猜图"
    ]
    return "\n".join(help_lines)


# try:
#     handler_mc.main()
#     handler_dc.main()
# finally:
#     saveSessions()