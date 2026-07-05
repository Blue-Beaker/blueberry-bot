from pydantic import BaseModel
from urllib.parse import urlparse


class Config(BaseModel):
    """Plugin configuration for bbot_render.

    Loaded from nonebot plugin config (e.g. bot_config.toml / .env).
    """
    render_server_uri:str="http://localhost:9081"
    render_server_timeout:int=30