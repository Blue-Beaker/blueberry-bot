import json
import os
import random
import threading
import time
from typing import Any, TypeVar
from nonebot import on_command,logger,on_startswith,get_plugin_config,on_type,get_adapter
from nonebot.rule import is_type
from nonebot.adapters import Message,Event,Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
import nonebot.config
from nonebot import get_driver,require
from nonebot.internal.matcher import Matcher

from .config import Config

from . import plat_sheets,levelid_filler

from .data_cache import BaseCache
from .utils import select_page

require('bbot_api')
from ..bbot_api.argparse import ArgumentError,ArgParser
from ..bbot_api import TextImageMessage,supportsImage,safeInt
from .. import bbot_api
require('gd_api')
from ..gd_api import gd,thumbs

from . import gd_data
from . import underrated
from . import gd_extras,gduser,platsearch,gdmusic,gdsearch,plat_rank
from nonebot import require
require("bbot_help")
from ..bbot_help import addHelpFunc,HelpRegistry
from .gdhelp import GD_HELP
from .sheets_data import gddl_backup

_KEEP_IMPORTS=[
    plat_sheets,levelid_filler,gd_data,underrated,gd_extras,gduser,platsearch,gdmusic,gdsearch,plat_rank
]

plugin_config = get_plugin_config(Config)

driver=get_driver()

gdhelp_cmd=on_command("gdhelp")
@gdhelp_cmd.handle()
async def _(bot:Bot, event:Event):
    await gdhelp_cmd.finish("\n".join(await GD_HELP.getAllHelp(bot,event)))
@addHelpFunc
def get_help():
    return ["gdhelp 查看GD查询相关命令帮助"
            "plathelp 查看Platformer搜索相关命令帮助"]
