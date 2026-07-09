from nonebot.adapters import Event,Bot,Message
from nonebot.adapters.discord import GuildMessageCreateEvent,MessageEvent as DCMessageEvent,Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment,MessageEvent as OBMessageEvent
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment
from nonebot.adapters.minecraft import BaseChatEvent as MCBaseChatEvent

def record(bot:Bot,content:bytes,filename:str="say.wav"):
    if isinstance(bot,OBBot):
        return OBMessageSegment.record(content)
    elif isinstance(bot,DCBot):
        return DCMessageSegment.attachment(filename,None,content)
    elif isinstance(bot,QQBot):
        return QQMessageSegment.file_audio(content,file_name=filename)
    else:
        return "无法发送音频: 不支持的平台."