import random
import time
from typing import Any, TypeVar
import uuid
from nonebot import get_plugin_config,logger,require
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Bot as OBBot
from nonebot.adapters.onebot.v11.message import Message,MessageSegment
from nonebot.exception import MockApiException

from nonebot.adapters.discord import Bot as DCBot,MessageSegment as DCMessageSegment,Message as DCMessage
from nonebot.adapters.discord.message import parse_message

from .config import Config

require("bbot_api")
from ..bbot_api import pack_message

require("bbot_render")
from ..bbot_render import RenderAPI

plugin_config = get_plugin_config(Config)

RENDERER=RenderAPI(plugin_config.render_server_uri)

_CHOICES=["⭐","🌙","😈","💎","🫐","🍓"]

def get_random_suffix():
    return f"你并没有获得{random.randint(1,500)}{random.choice(_CHOICES)}"

@Bot.on_calling_api
async def handle_api_call(bot: Bot, api: str, data: dict[str, Any]):
    # print(api,data)
    if not isinstance(bot, OBBot):
        return
    
    # logger.info(data)
    
    if(api in ["send_msg"]):
        msg=data.get("message")
        if isinstance(msg,Message):
            
            if msg.extract_plain_text().strip():
                msg=msg+"\n"+get_random_suffix()
            elif msg[0].type == "node":
                msg=msg+await pack_message(bot,get_random_suffix())
                
            data["message"]=await convertMessage(msg)
            
    # logger.info(data)
    
    # raise MockApiException(data)
                
    # logger.info(f"{api},{data}")
    
async def convertMessageNode(msg:Message):
    return msg

    newmsg=Message()
    for msgseg1 in msg:
        msg1 = msgseg1.data.get("content",None)
        if msg1:
            newmsg.append(MessageSegment.node_custom(int(msgseg1.data["user_id"]),msgseg1.data["nickname"],await convertMessage(msg1)))
            
    return newmsg
    

async def convertMessage(msg:Message):
    if msg.__len__()==0:
        return msg
            
    if getattr(msg[0],'type',None) == "node":
        return await convertMessageNode(msg)
    
    newmsg=Message()
    
    strings_pool=""
    for seg in msg:
        if isinstance(seg,str):
            strings_pool+=seg
        elif seg.is_text():
            strings_pool+=seg.data["text"]
        else:
            if strings_pool:
                newmsg.append(await convertMessageSegment(strings_pool))
                strings_pool=""
            newmsg.append(await convertMessageSegment(seg))
    
    if strings_pool:
        newmsg.append(await convertMessageSegment(strings_pool))
    return newmsg
    
async def convertMessageSegment(seg:MessageSegment|str):
    if isinstance(seg,str):
        text=seg
    elif seg.is_text():
        text=seg.data["text"]
    else:
        return seg
        
    imgid=uuid.uuid4().hex
    img=await RENDERER.render_text(imgid,text)
    # print(type(img))
    if isinstance(img,bytes):
        return MessageSegment.image(img)
                    
    return seg


                
if plugin_config.debug_hook_discord:
    logger.info("Enable discord hook for testing...")
    @Bot.on_calling_api
    async def _debug_with_dc(bot: Bot, api: str, data: dict[str, Any]):
        if isinstance(bot,DCBot) and (api in 'create_message'):
            text_content=data.get('content',None)
            if text_content:
                text_content=text_content+"\n"+get_random_suffix()
                
                imgid=uuid.uuid4().hex
                img=await RENDERER.render_text(imgid,text_content)
                if isinstance(img,bytes):
                    imageSegment=DCMessageSegment.attachment("text.png",content=img)
                    
                    data.pop('content')
                    
                    data2=parse_message(imageSegment)
                    
                    new_attachments=[]
                    new_attachments.extend(data2.get("attachments",[]))
                    new_attachments.extend(data.get("attachments",[]))
                    data["attachments"]=new_attachments
                    
                    new_files=[]
                    new_files.extend(data2.get("files",[]))
                    new_files.extend(data.get("files",[]))
                    data["files"]=new_files
                    
                    return