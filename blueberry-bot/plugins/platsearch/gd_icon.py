from enum import Enum
from nonebot import get_plugin_config
import requests
from pydantic import BaseModel, field_validator

class Config(BaseModel):
    icon_server_base_url:str="http://127.0.0.1:8888/icon"
    
module_config=get_plugin_config(Config)


    
class IconType(Enum):
    CUBE="cube"
    SHIP="ship"
    BALL="ball"
    UFO="ufo"
    WAVE="wave"
    ROBOT="robot"
    SPIDER="spider"
    SWING="swing"
    JETPACK="jetpack"
    
ICON_TYPES=[
        IconType.CUBE,
        IconType.SHIP,
        IconType.BALL,
        IconType.UFO,
        IconType.WAVE,
        IconType.ROBOT,
        IconType.SPIDER,
        IconType.SWING,
        IconType.JETPACK]

def construct_icon_url(gamemode:IconType,id:int,col1:int,col2:int,glow:int=-1):

    iconurl = f"{module_config.icon_server_base_url}?gamemode={gamemode.value}&id={id}&primary={col1}&secondary={col2}"
    if glow>=0:
        iconurl += f"&glow={glow}"
    return iconurl

def get_icon(gamemode:IconType,id:int,col1:int,col2:int,glow:int=-1):
    url=construct_icon_url(gamemode,id,col1,col2,glow)
    req = requests.get(url=url, timeout=10)
    if req.status_code!=200:
        return None
    return req.content if isinstance(req.content,bytes) else None