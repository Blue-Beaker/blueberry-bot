from typing import Type, Union
from nonebot.adapters import Bot
from nonebot.adapters.discord import Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.onebot.v11 import Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment
from nonebot.adapters.minecraft import Bot as MCBot, Message as MCMessage

from .backends.base import BaseTextImageMessage as TextImageMessage
from .backends.minecraft import MCTextImageMessage
from .backends.onebot import OBTextImageMessage
from .backends.discord import DCTextImageMessage
from .backends.qq import QQTextImageMessage

from .backends import base

def supportsRecord(bot:Bot):
    return isinstance(bot,OBBot) or isinstance(bot,DCBot) or isinstance(bot,QQBot)
def supportsImage(bot:Bot):
    return isinstance(bot,OBBot) or isinstance(bot,DCBot) or isinstance(bot,QQBot)
def supportsLowImage(bot:Bot):
    return supportsImage(bot) or isinstance(bot,MCBot)
def supportsFile(bot:Bot):
    return isinstance(bot,DCBot) or isinstance(bot,QQBot)

def supportsMarkdown(bot:Bot):
    return isinstance(bot,DCBot)

def file(bot:Bot,content:bytes,filename:str):
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

MESSAGE_TYPE=Union[DCMessage,OBMessage,QQMessage,MCMessage,str]

def build(bot:Bot):
    if isinstance(bot,DCBot):
        return DCTextImageMessage()
    elif isinstance(bot,OBBot):
        return OBTextImageMessage()
    elif isinstance(bot,QQBot):
        return QQTextImageMessage()
    else:
        return TextImageMessage("",type(bot))
        
base.BUILD_FUNC=build