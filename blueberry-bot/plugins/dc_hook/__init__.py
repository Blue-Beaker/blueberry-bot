import asyncio
from typing import Any, Dict, Optional
from nonebot import get_plugin_config,logger,require
from nonebot.adapters import Bot

from nonebot.adapters.discord import Bot as DCBot
from nonebot.exception import NetworkError

from .config import Config

require("bbot_api")

require("bbot_render")



plugin_config = get_plugin_config(Config)

@Bot.on_called_api
async def handle_api_result(
    bot: Bot, exception: Optional[Exception], api: str, data: Dict[str, Any], result: Any
):
    if not isinstance(bot, DCBot):
        return
    if exception is not None:
        logger.error(f"API call {api} failed with exception: {exception}")
    if isinstance(exception, NetworkError):
        logger.warning(f"Network error occurred during API call {api}. Retrying...")
        retries = getattr(data, "_dchook_retries", 0)
        if retries > plugin_config.max_msg_retries:
            logger.error(f"API call {api} failed after {plugin_config.max_msg_retries} retries.")
            
        retries += 1
        interval = plugin_config.msg_retry_interval + retries * plugin_config.msg_retry_interval_increment
        await asyncio.sleep(interval)
        
        await bot.call_api(api, **data, _dchook_retries=retries)
        logger.info(f"API call {api} succeeded on retry {retries}.")
        return
    