import random
import time
from typing import Any
from nonebot import get_plugin_config,logger,require
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Bot as OBBot
from nonebot.adapters.onebot.v11.message import Message,MessageSegment
from .config import Config

require("bbot_api")
from ..bbot_api import pack_message


plugin_config = get_plugin_config(Config)

@OBBot.on_calling_api
async def handle_api_call(bot: Bot, api: str, data: dict[str, Any]):
    if not isinstance(bot, OBBot):
        return
    # print(api,type(data.get("message")))
    if(api in ["send_msg"]):
        msg=data.get("message")
        if isinstance(msg,Message):
            choices=["⭐","🌙","😈","💎","🫐","🍓"]
            
            if msg.extract_plain_text().strip():
                data["message"]=msg+"\n"+f"你并没有获得{random.randint(1,500)}{random.choice(choices)}"
            elif msg[0].type == "node":
                data["message"]=msg+await pack_message(bot,f"你并没有获得{random.randint(1,500)}{random.choice(choices)}")
        
    # logger.info(f"{api},{data}")