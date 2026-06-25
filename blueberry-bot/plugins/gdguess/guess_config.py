from typing import Any
from nonebot import require

from .guess_session import ConfigEntry,ConfigManager as LegacyConfigManager

require("bbot_api")
from ..bbot_api.group_config import GroupConfig,ConfigItem,make_config_handler

class GDGuessConfigItem(ConfigItem):
    cooldown:int=60
    
class ConfigManager(GroupConfig[GDGuessConfigItem]):
    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(GDGuessConfigItem, config_path)
        
    def migrate(self,manager:LegacyConfigManager):
        for group,e in manager.entries.items():
            self.get_for_edit(group).load_dict(e.to_dict())
            
    def get_or_create(self,id:str,default_data:dict[str,Any]={}):
        if id not in self.group_overrides:
            self.group_overrides[id] = self.config_class().load_dict(default_data)
        return self.get_for_edit(id)