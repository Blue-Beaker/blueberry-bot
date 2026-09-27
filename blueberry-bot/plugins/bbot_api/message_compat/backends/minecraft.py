from nonebot import require

from typing import Generic, Type, TypeVar, Union
import uuid
from nonebot import logger
from nonebot.adapters import Event,Bot,Message

from nonebot.matcher import Matcher
from ..buttons import ButtonKeyboard,KBButton
from nonebot.adapters.minecraft import Bot as MCBot, BaseChatEvent as MCBaseChatEvent, Message as MCMessage, MessageSegment as MCMessageSegment

from .base import BaseTextImageMessage

try:
    require("bbot_mc_image")
    from ....bbot_mc_image import image_to_mc_text
except:
    image_to_mc_text=None

class MCTextImageMessage(BaseTextImageMessage[MCMessage]):
    def __init__(self) -> None:
        super().__init__(MCMessage(),MCBot)
        
    def addImage(self,image:bytes,image_name:str="",small:bool=False):
        if image_to_mc_text is not None:
            self.msg+=("\n"+image_to_mc_text("[image]",image))
        return self