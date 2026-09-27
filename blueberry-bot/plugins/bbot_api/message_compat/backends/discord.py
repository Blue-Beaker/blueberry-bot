import uuid
from nonebot.adapters.discord import Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot

from ..utils import escapeMarkdown
from .base import BaseTextImageMessage

class DCTextImageMessage(BaseTextImageMessage[DCMessage]):
    def __init__(self) -> None:
        super().__init__(DCMessage(),DCBot)
    def addText(self,text:str,markdown:bool=False):
        if not markdown:
            self.msg.append(escapeMarkdown(text))
        else:
            self.msg.append(text)
        return self
    
    def addImage(self,image:bytes,image_name:str="",small:bool=False):
        if not image_name:
            image_name=uuid.uuid4().hex+".png"
        self.msg.append(DCMessageSegment.attachment(image_name,content=image))
        return self