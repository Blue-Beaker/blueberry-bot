from pydantic import BaseModel
from urllib.parse import urlparse


class Config(BaseModel):
    """Plugin configuration for bbot_render.

    Loaded from nonebot plugin config (e.g. bot_config.toml / .env).
    """
    render_resource_url: str = "http://127.0.0.1:9081/resources"
    render_resource_alt_url: str = ""
