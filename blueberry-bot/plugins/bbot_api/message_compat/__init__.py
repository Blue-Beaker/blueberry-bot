import uuid
from nonebot.adapters import Event,Bot,Message
from nonebot.adapters.discord import GuildMessageCreateEvent,MessageEvent as DCMessageEvent,Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment,MessageEvent as OBMessageEvent
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment
from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent
from nonebot.matcher import Matcher
from .images import get_images_from_message,ImageFile

def supportsRecord(bot:Bot):
    return isinstance(bot,OBBot) or isinstance(bot,DCBot) or isinstance(bot,QQBot)
def supportsImage(bot:Bot):
    return isinstance(bot,OBBot) or isinstance(bot,DCBot) or isinstance(bot,QQBot)
def supportsFile(bot:Bot):
    return isinstance(bot,DCBot) or isinstance(bot,QQBot)

def supportsMarkdown(bot:Bot):
    return isinstance(bot,DCBot)

def file(bot:Bot,content:bytes,filename:str):
    # if isinstance(bot,OBBot):
    #     return OBMessageSegment.record(content)
    if isinstance(bot,DCBot):
        return DCMessageSegment.attachment(filename,None,content)
    elif isinstance(bot,QQBot):
        return QQMessageSegment.file_file(content,file_name=filename)
    else:
        return "无法发送文件: 不支持的平台."
    

def record(bot:Bot,content:bytes,filename:str,as_file:bool=False):
    if isinstance(bot,OBBot):
        return OBMessageSegment.record(content)
    elif isinstance(bot,DCBot):
        return DCMessageSegment.attachment(filename,None,content)
    elif isinstance(bot,QQBot):
        if as_file:
            return QQMessageSegment.file_file(content,file_name=filename)
        return QQMessageSegment.file_audio(content,file_name=filename)
    else:
        return "无法发送音频: 不支持的平台."
    
class TextImageMessage:
    msg:DCMessage|OBMessage|QQMessage|str
    def __init__(self,msg:DCMessage|OBMessage|QQMessage|str) -> None:
        self.msg=msg
    @classmethod
    def build(cls,bot:Bot):
        if isinstance(bot,DCBot):
            return cls(DCMessage())
        elif isinstance(bot,OBBot):
            return cls(OBMessage())
        elif isinstance(bot,QQBot):
            return cls(QQMessage())
        else:
            return cls("")
    def addText(self,text:str):
        if isinstance(self.msg,Message):
            self.msg.append(text)
        else:
            self.msg+=text
        return self
    def addLine(self,text:str):
        if self.msg.__len__()>0 and (isinstance(self.msg,str) or self.msg[-1].is_text()):
            self.addText("\n")
        self.addText(text)
        return self
    def addImage(self,image:bytes,image_name:str="",small:bool=False):
        if isinstance(self.msg,DCMessage):
            if not image_name:
                image_name=uuid.uuid4().hex+".png"
            self.msg.append(DCMessageSegment.attachment(image_name,content=image))
        elif isinstance(self.msg,OBMessage):
            if small:
                imgsegment=OBMessageSegment.image(image)
                imgsegment.data["sub_type"]=1
                self.msg.append(imgsegment)
            else:
                self.msg.append(OBMessageSegment.image(image))
        elif isinstance(self.msg,QQMessage):
            self.msg.append(QQMessageSegment.file_image(image,image_name))
        return self
    def getMessage(self):
        return self.msg
    def getPlainText(self):
        if isinstance(self.msg,Message):
            return self.msg.extract_plain_text()
        else:
            return self.msg
    
    async def send(self,matcher:type[Matcher],**kwargs):
        if isinstance(self.msg,QQMessage):
            msgpart=QQMessage()
            has_image=False
            for i in self.msg:
                if has_image and not i.is_text():
                    # Send part of message
                    await matcher.send(msgpart,**kwargs)
                    msgpart=QQMessage()
                        
                msgpart.append(i)
                if not i.is_text():
                    has_image=True
                    
        
        await matcher.send(self.msg,**kwargs)
        
    async def finish(self,matcher:type[Matcher],**kwargs):
        await self.send(matcher,**kwargs)
        await matcher.finish()