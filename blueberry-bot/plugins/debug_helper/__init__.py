from nonebot import require,get_plugin_config
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
    debuglist=plugin_config.debug_sessions
    try:
        eid = getid(event)
        is_listed=(eid in debuglist)
        
        if is_listed!=plugin_config.debug_sessions_is_on:
            raise IgnoredException(f"Blocked: {eid}")
    except:
        pass