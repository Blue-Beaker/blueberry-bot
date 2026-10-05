import random
import time
from typing import Any, TypeVar
import uuid
from nonebot import get_plugin_config,logger,require
from nonebot.adapters import Bot
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage
from nonebot.exception import MockApiException

from .config import Config
from . import patch

import re

plugin_config = get_plugin_config(Config)

_CHOICES=["⭐","🌙","😈","💎","🫐","🍓"]

PATTERN_URL=re.compile(r"[\w\.-]+\.[a-zA-Z]+(?=\/[\w\.\/]+)")

@Bot.on_calling_api
async def handle_api_call(bot: Bot, api: str, data: dict[str, Any]):
    if not isinstance(bot, QQBot):
        return
    
    # print(api,data)
    
    # logger.info(data)
    
    if(api in ["post_group_messages","post_c2c_messages"]):
        content=data.get("content")
        if not content:
            return
        data["content"]=re.sub(PATTERN_URL,replace,content)
        
def replace(matched:re.Match[str]):
    string=matched.group(0)
    return ''.join([random.choice(_CHOICES) for i in string])