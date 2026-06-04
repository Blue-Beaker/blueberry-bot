from nonebot import logger, require,get_plugin_config
from nonebot.exception import IgnoredException
from nonebot.message import run_preprocessor
from nonebot.adapters import Event
from nonebot.matcher import Matcher
from .config import Config

plugin_config=get_plugin_config(Config)

require("bbot_api")
from ..bbot_api import getid

@run_preprocessor
async def _(event: Event, matcher: Matcher):
    if matcher.module_name and matcher.module_name.split(".")[-1] in plugin_config.debug_always_allowed_plugins:
        return
    debuglist=plugin_config.debug_sessions
    try:
        eid = getid(event)
        is_listed=(eid in debuglist)
        
        if is_listed!=plugin_config.debug_sessions_is_on:
            # logger.info(f"Ignored {event} from {eid}")
            raise IgnoredException(f"Blocked: {eid}")
    except Exception as e:
        if isinstance(e,IgnoredException):
            raise e
        pass