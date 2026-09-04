from pathlib import Path

from ..file_based_cache import FileBasedCache
from .gddl_internal import GDDLSearchResult,getGDDLResponse,fetch_gddl_all_plat,safeFloat,safeInt
from .. import run_async
from .models import GDDLLevel,GDDLSearchLevel

from nonebot import require,get_driver

# TODO: rework to adapt new GDDL API

def parseLevelData(data:list[dict]|None):
    if not data:
        return None
    levels:dict[int,GDDLLevel]={}
    for l in data:
        level=GDDLSearchLevel.from_dict(l).to_gddl_level()
        levels[level.ID]=level
    return levels
    