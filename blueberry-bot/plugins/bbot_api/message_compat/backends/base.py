from typing import Callable, Generic, Type, TypeVar, Union
import uuid
from nonebot import logger
from nonebot.adapters import Event,Bot,Message

from nonebot.matcher import Matcher
from ..buttons import ButtonKeyboard,KBButton

MESSAGE_TYPE=Union[Message,str]
_T=TypeVar("_T",bound=Message|str)

class BaseTextImageMessage(Generic[_T]):
    msg:_T
    bot_type:Type[Bot]
    def __init__(self,msg:_T,bot_type:Type[Bot]) -> None:
        self.msg=msg
        self.bot_type=bot_type
    @classmethod
    def build(cls,bot:Bot) -> "BaseTextImageMessage":
        if BUILD_FUNC:
            return BUILD_FUNC(bot)
        return cls("",type(bot)) # type: ignore
    def append(self,text:str,markdown:bool=False):
        return self.addLine(text,markdown=markdown)
    def addText(self,text:str,markdown:bool=False):
        if isinstance(self.msg,Message):
            self.msg.append(text)
        else:
            self.msg+=text # type: ignore
        return self
    def addLine(self,text:str,markdown:bool=False):
        if self.msg.__len__()>0 and (isinstance(self.msg,str) or self.msg[-1].is_text()):
            self.addText("\n")
        self.addText(text,markdown=markdown)
        return self
    
    def addImage(self,image:bytes,image_name:str="",small:bool=False):
        return self
    
    def getMessage(self):
        return self.msg
    def getPlainText(self):
        if isinstance(self.msg,Message):
            return self.msg.extract_plain_text()
        else:
            return self.msg
        
    def addButtons(self,buttons:ButtonKeyboard):
        return self
            
    def supportsButton(self) -> bool:
        return False
    
    def addButton(self,button:KBButton):
        return self
            
    async def send(self,matcher:type[Matcher]|Matcher,**kwargs):
        await matcher.send(self.msg,**kwargs)
        
    async def finish(self,matcher:type[Matcher]|Matcher,**kwargs):
        await self.send(matcher,**kwargs)
        await matcher.finish()
        
BUILD_FUNC:Callable[[Bot],BaseTextImageMessage]|None=None