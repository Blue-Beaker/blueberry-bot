from nonebot.adapters.discord import Bot as DCBot,GuildMessageCreateEvent
from nonebot.adapters.discord.api.model import Attachment
from nonebot.adapters.onebot.v11 import Bot as OBBot, MessageSegment as OBMessageSegment,Message as OBMessage
from nonebot.adapters.qq import Bot as QQBot, MessageSegment as QQMessageSegment, Message as QQMessage
from nonebot.adapters.qq.message import Attachment as QQAttachment

from nonebot.internal.adapter import Bot,Event,Message

from typing import Tuple

import requests
import hashlib


def get_image_ext(image: bytes) -> str:
    """根据图片文件头判断扩展名."""
    if len(image) < 12:
        return ".png"
    # PNG: 8-byte signature
    if image[:8] == b'\x89PNG\r\n\x1a\n':
        return ".png"
    # JPEG: starts with FF D8
    if image[:2] == b'\xff\xd8':
        return ".jpg"
    # GIF: GIF87a or GIF89a
    if image[:6] in (b'GIF87a', b'GIF89a'):
        return ".gif"
    # WEBP: RIFF ... WEBP
    if image[:4] == b'RIFF' and image[8:12] == b'WEBP':
        return ".webp"
    # BMP: BM
    if image[:2] == b'BM':
        return ".bmp"
    return ".png"


def make_image_filename(image: bytes) -> str:
    """根据图片内容计算 md5 并检测扩展名，生成文件名."""
    md5 = hashlib.md5(image).hexdigest()
    ext = get_image_ext(image)
    return f"{md5}{ext}"


class ImageFile:
    image:bytes
    filename:str
    def __init__(self,image:bytes,filename:str) -> None:
        self.image=image
        self.filename=filename


async def get_images_from_message(bot:Bot, event:Event, msg:Message, count:int|None=None) -> Tuple[list[ImageFile],list[str]]:
    images:list[ImageFile]=[]
    errors:list[str]=[]
    imgs=None
    if isinstance(msg,OBMessage):
        imgs=msg.get("image",count)
    elif isinstance(msg,QQMessage):
        imgs=msg.get("image",count)
    elif isinstance(event,GuildMessageCreateEvent):
        imgs=[atta for atta in event.attachments if isinstance(atta.content_type,str) and atta.content_type.startswith('image')]
    if not imgs:
        return [],[]
    
    imgs=imgs[0:count] if count else imgs
    for img in imgs:
        filename=None
        imageFile=None
        
        if isinstance(img,QQAttachment) and isinstance(bot,QQBot):
            url=img.data.get("url")
            if not url:
                errors.append("找不到URL.")
                continue
            resp=requests.get(url)
            filename=make_image_filename(resp.content)
            images.append(ImageFile(resp.content,filename))
        
        elif isinstance(img,OBMessageSegment) and isinstance(bot,OBBot):
            filename=img.data.get("file")
            if filename:
                imgdata = await bot.get_image(file=filename)
                url=imgdata.get('url')
                if not url:
                    errors.append("找不到URL.")
                    continue
                    
                resp=requests.get(url)
                images.append(ImageFile(resp.content,filename))
                
        elif isinstance(img,Attachment) and isinstance(bot,DCBot):
            resp=requests.get(img.url)
            
            filename=img.filename
            images.append(ImageFile(resp.content,img.filename))
    return images,errors