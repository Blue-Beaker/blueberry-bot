from typing import Any
from nonebot import get_plugin_config,logger
from nonebot.adapters import Bot
from nonebot.adapters.minecraft.bot import Bot as MCBot
from config import Config

plugin_config = get_plugin_config(Config)
prefix=plugin_config.mc_message_prefix

@MCBot.on_calling_api
async def handle_api_call(bot: Bot, api: str, data: dict[str, Any]):
    if(api in ["send_msg","send_private_msg"]):
        data["message"]=prefix+data["message"]
    logger.info(f"{api},{data}")