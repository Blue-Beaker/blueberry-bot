from typing import Type, Union
import uuid
from nonebot import logger
from nonebot.adapters import Event,Bot,Message
from nonebot.adapters.discord import GuildMessageCreateEvent,MessageEvent as DCMessageEvent,Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.discord.api import Button,ButtonStyle

from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment,MessageEvent as OBMessageEvent

from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment

from nonebot.adapters.minecraft import Bot as MCBot, BaseChatEvent as MCBaseChatEvent, Message as MCMessage, MessageSegment as MCMessageSegment
from .base import BaseTextImageMessage

class OBTextImageMessage(BaseTextImageMessage[OBMessage]):
    def __init__(self) -> None:
        super().__init__(OBMessage(),OBBot)
    def addImage(self,image:bytes,image_name:str="",small:bool=False):
        if small:
            imgsegment=OBMessageSegment.image(image)
            imgsegment.data["sub_type"]=1
            self.msg.append(imgsegment)
        else:
            self.msg.append(OBMessageSegment.image(image))
        return self