

import json
import os
from nonebot import logger, on_command, get_driver
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg

from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent
from nonebot.adapters.discord import MessageEvent as DCMessageEvent, Bot as DCBot, MessageSegment as DCMessageSegment, Message as DCMessage

from . import guess_data
from . import handler_mc
from . import handler_dc
from . import handler_base
from .handler_base import INSTANCES,guess_command

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
    manager=INSTANCES.getOrCreateGuessManager(get_group_id(event))
    
    message=args.extract_plain_text().strip()
    logger.debug(f"'{message}' from{event}")
    feedBackMessage = guess_command(message,manager)
    
    if(feedBackMessage):
        if isinstance(event,DCMessageEvent):
            split=feedBackMessage.split("{username}")
            msgseg=split[0]
            for segment in split[1:]:
                msgseg=msgseg+DCMessageSegment.mention_user(event.user_id)+DCMessageSegment.text(segment)
            await handler_msg.send(msgseg)
        elif isinstance(event,MCBaseChatEvent):
            await handler_msg.send(f"{feedBackMessage}".replace("{username}",event.player.nickname))
        elif isinstance(event,OBGroupMessageEvent):
            await handler_msg.send(f"{feedBackMessage}".replace("{username}",f"[CQ:at,qq={event.user_id}]"))
        else:
            await handler_msg.send(feedBackMessage.replace("{username}",""))
        
    pass

def get_group_id(event:Event):
    if isinstance(event,MCBaseChatEvent):
        return "mc_"+event.server_name
    elif isinstance(event,DCMessageEvent):
        return "dc_"+str(event.channel_id)
    elif isinstance(event,OBGroupMessageEvent):
        return "onebot_"+str(event.group_id)
    else:
        return event.get_session_id()

# try:
#     handler_mc.main()
#     handler_dc.main()
# finally:
#     saveSessions()