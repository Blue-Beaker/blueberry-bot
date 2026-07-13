from nonebot import require
require("bbot_api")
from ..bbot_api.group_config import ConfigItem

class PermissionsEntry(ConfigItem):
    gd_unrated:bool=False