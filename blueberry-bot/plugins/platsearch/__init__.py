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

from . import underrated

from . import gd_extras,gduser,platsearch


plugin_config = get_plugin_config(Config)

driver=get_driver()

def get_help(bot:Bot,event:Event):
    help_lines=platsearch.get_help(bot,event)
    help_lines.extend(gd_extras.get_help(bot,event))
    help_lines.extend(gduser.get_help(bot,event))
    return help_lines