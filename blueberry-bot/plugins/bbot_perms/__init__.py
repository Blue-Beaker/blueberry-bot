import math
import time
from nonebot import get_plugin_config,get_driver, logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.discord.api.model import Attachment
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment,Message as OBMessage

from nonebot.internal.adapter import Bot,Event,Message
from nonebot.internal.matcher import Matcher

from typing import Type, Union
from nonebot.params import CommandArg
from nonebot import on_command, require
from pathlib import Path
from nonebot.permission import SUPERUSER
import random

import requests

import utils

require("bbot_api")
from ..bbot_api import TextImageMessage,getid,get_group_id
from ..bbot_api.group_config import GroupConfig,ConfigItem,make_config_handler
from ..bbot_api.profile_link.events import on_link, LinkUserEvent, LinkGroupEvent, UnlinkUserEvent, UnlinkGroupEvent

from .perms import PermissionsEntry

__plugin_meta__ = PluginMetadata(
    name="bbot_perms",
    description="",
    usage=""
)

    
CONFIG_PATH=Path("config")
CONFIG_PATH.mkdir(parents=True,exist_ok=True)

group_permissions = GroupConfig(PermissionsEntry,(CONFIG_PATH/"bbot_perms.json").__str__())

def get_perms(event:Event):
    return group_permissions.get(getid(event))

driver=get_driver()

@driver.on_startup
async def _():
    group_permissions.load()
    
@driver.on_shutdown
async def _():
    group_permissions.save()


require("bbot_help")
from ..bbot_help import SUPERUSER_HELP_REGISTRY
@SUPERUSER_HELP_REGISTRY.addHelpFunc
def _():
    return "perms 管理一般权限"
    
perms=on_command("perms",permission=SUPERUSER)
config_handler=make_config_handler("perms",PermissionsEntry,group_permissions,get_groupid_function=getid)
perms.handle()(config_handler)