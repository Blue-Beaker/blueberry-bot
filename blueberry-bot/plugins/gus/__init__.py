import math
import time
from nonebot import get_plugin_config,get_driver, logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters.discord import Message as DCMessage,Bot as DCBot,MessageSegment as DCMessageSegment,GuildMessageCreateEvent
from nonebot.adapters.discord.api.model import Attachment
from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent as OBGroupMessageEvent,MessageSegment as OBMessageSegment,Message as OBMessage

from nonebot.internal.adapter import Bot,Event,Message
from nonebot.internal.matcher import Matcher

from typing import Type, Union
from nonebot.params import CommandArg
from nonebot import on_command, require
from pathlib import Path
from nonebot.permission import SUPERUSER
import random

import requests

import utils

from .config import Config
from .gus_data import GusData,GusEntry

require("bbot_api")
from ..bbot_api import TextImageMessage,getid,get_group_id
from ..bbot_api.group_config import GroupConfig,ConfigItem,make_config_handler

require("gdguess")
from ..gdguess import gdguess_logic

try:
    require("orb_api")
    from .. import orb_api
except:
    orb_api=None

__plugin_meta__ = PluginMetadata(
    name="gus",
    description="",
    usage="",
    config=Config,
)

class GusConfigItem(ConfigItem):
    cooldown:int=300
    
CONFIG_PATH=Path("config/gus")
CONFIG_PATH.mkdir(parents=True,exist_ok=True)

group_config = GroupConfig(GusConfigItem,(CONFIG_PATH/"group_config.json").__str__())

gus__data = GusData(CONFIG_PATH/"gus_data.json",CONFIG_PATH/"img")

driver=get_driver()

@driver.on_startup
async def _():
    group_config.load()
    gus__data.load()
    
@driver.on_shutdown
async def _():
    group_config.save()
    gus__data.save()
    
    
class GusCooldown:
    last_gus_time:dict[str,int]={}
    def combine_id(self,gid:str,uid:str):
        return gid+"_"+uid
    
    def getAvailableTime(self,gid:str,uid:str):
        cid=self.combine_id(gid,uid)
        last_time=self.last_gus_time.get(cid,0)
        return group_config.get(gid).cooldown+last_time
        
    def getRemainingCooldown(self,gid:str,uid:str):
        cid=self.combine_id(gid,uid)
        last_time=self.last_gus_time.get(cid,0)
        return last_time+group_config.get(gid).cooldown-int(math.floor(time.time()))
        
    def canUse(self,gid:str,uid:str):
        if time.time() < self.getAvailableTime(gid,uid):
            return False
        return True
    def use(self,gid:str,uid:str):
        cid=self.combine_id(gid,uid)
        self.last_gus_time[cid]=int(math.floor(time.time()))
    def tryUse(self,gid:str,uid:str):
        if self.canUse(gid,uid):
            self.use(gid,uid)
            return True
        return False
    
cooldown = GusCooldown()

gus_cmd=on_command("gus")
@gus_cmd.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    text = msg.extract_plain_text()
    if text:
        await gdguess_logic(gus_cmd,bot,event,msg)
    else:
        await gus_logic(gus_cmd,bot,event,msg)
    pass

async def gus_logic(matcher:Type[Matcher],bot:Bot,event:Event,msg:Message=CommandArg()):
    group_id = get_group_id(event)
    user_id=event.get_user_id()
    
    if not cooldown.canUse(group_id,user_id):
        cd=cooldown.getRemainingCooldown(group_id,user_id)
        await matcher.finish(f"别Gu啦, {cd}秒后再来吧! 或者来猜猜关卡? (本指令可当作-gdguess)")
    
    entries=gus__data.get_entries()
    
    if not entries:
        await matcher.finish(f"错误: 找不到Gus")
    
    
    key,entry=random.choice(list(entries.items()))
    img=gus__data.get_img(key)
    
    reply=TextImageMessage.build(bot)
    reply.addLine(f"抓到一只Gus!")
    reply.addLine(entry.name)
    reply.addLine(entry.desc)
    if img:
        reply.addImage(img,entry.file,small=True)
    else:
        reply.addLine("呜呜, Gus溜走了! (图片不存在)")
        
    cooldown.use(group_id,user_id)
    
    if orb_api:
        orb_id=orb_api.get_orb_owner_id(event)
        if orb_id:
            add_orbs=random.randint(1,10)
            orb_api.add_balance(orb_id,add_orbs)
            reply.addLine(f"你获得了 {add_orbs} Orbs")
    
    await matcher.finish(reply.getMessage(), at_sender=True)
    
    
gus_add=on_command("gus-add",permission=SUPERUSER)
@gus_add.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    text=msg.extract_plain_text()
    
    update=False
    if text.startswith("-u"):
        text=text.removeprefix("-u").strip()
        update=True
    
    spl=text.split(",",2)
    
    if spl.__len__()<3:
        await gus_add.finish("需要3个参数: key, name, desc 用,分隔")
    
    entry=GusEntry()
    key=spl[0].removesuffix("\n").lower().replace("-","_").strip()
    entry.name=spl[1].removesuffix("\n").strip()
    entry.desc=spl[2].removesuffix("\n").strip()
    
    existing_entry=gus__data.get_data(key)
    if existing_entry:
        if not update:
            await gus_add.finish(f"ID '{key}' 已存在, 加入-u前缀以更新: {existing_entry.name}.")
        else:
            orig_name=existing_entry.name
            orig_desc=existing_entry.desc
            
            existing_entry.name=entry.name
            existing_entry.desc=entry.desc
            gus__data.save()
            await gus_add.finish(f"已更新 '{key}': {existing_entry.name}.")
    elif update:
        await gus_add.finish(f"未找到 ID '{key}'.")
        
    imgs=None
    if isinstance(msg,OBMessage):
        imgs=msg.get("image",1)
    elif isinstance(event,GuildMessageCreateEvent):
        imgs=[atta for atta in event.attachments if atta.content_type.startswith('image')]
    if not imgs:
        await gus_add.finish("请包含一张图片用于添加.")
    
    img=imgs[0]
    
    filename=None
    imageFile=None
    
    if isinstance(img,OBMessageSegment) and isinstance(bot,OBBot):
        filename=img.data.get("file")
        if filename:
            imgdata = await bot.get_image(file=filename)
            url=imgdata.get('url')
            if not url:
                await gus_add.finish("内部错误: 找不到URL.")
                
            resp=requests.get(url)
            imageFile=resp.content
            entry.file=filename
            
    elif isinstance(img,Attachment) and isinstance(bot,DCBot):
        resp=requests.get(img.url)
        
        filename=img.filename
        imageFile=resp.content
        entry.file=img.filename
            
            # logger.info(repr(type(img))+repr(img))
    if filename and isinstance(imageFile,bytes):
        gus__data.add_entry(key,entry,imageFile)
        logger.info(f"Adding gus entry: {entry}")
        gus__data.save()
        
        reply=TextImageMessage.build(bot)
        reply.addLine("添加成功!")
        reply.addLine(entry.name)
        reply.addLine(entry.desc)
        reply.addLine(entry.file)
        reply.addImage(imageFile,filename,small=True)
        
        await gus_add.finish(reply.getMessage())
    
    if not imgs:
        await gus_add.finish("添加失败.")
        
gus_get=on_command("gus-get",permission=SUPERUSER)
@gus_get.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    text=msg.extract_plain_text()
    reply=TextImageMessage.build(bot)
    if not text:
        for k,v in gus__data.get_entries().items():
            reply.addLine(f"{k}:{v.name}")
        await gus_get.finish(reply.getMessage())
        
    key=text.removesuffix("\n").lower().replace("-","_").strip()
    
    entry=gus__data.get_data(key)
    img=gus__data.get_img(key)
    if entry:
        reply.addLine(key)
        reply.addLine(entry.name)
        reply.addLine(entry.desc)
    else:
        reply.addLine(f"未找到 ID '{key}'.")
        
    if img:
        reply.addImage(img)
    await gus_get.finish(reply.getMessage())

gus_rm=on_command("gus-rm",permission=SUPERUSER)
@gus_rm.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    text=msg.extract_plain_text()
    reply=TextImageMessage.build(bot)
    if not text:
        for k,v in gus__data.get_entries().items():
            reply.addLine(f"{k}:{v}")
        await gus_rm.finish(reply.getMessage())
        
    key=text.removesuffix("\n").lower().replace("-","_").strip()
    
    entry=gus__data.remove_entry(key)
    gus__data.save()
    if entry:
        reply.addLine(key)
        reply.addLine(entry.name)
        reply.addLine(entry.desc)
        await gus_rm.finish(reply.getMessage())
    else:
        reply.addLine(f"未找到 ID '{key}'.")
        await gus_rm.finish(reply.getMessage())
    await gus_rm.finish(reply.getMessage())
    
gus_cfg=on_command("gus-cfg",permission=SUPERUSER)
config_handler=make_config_handler("gus-cfg",GusConfigItem,group_config)
gus_cfg.handle()(config_handler)


def get_help(bot:Bot,event:Event):
    help_lines=[
            "gus 抓一只gus",
            "gus [参数] 相当于gdguess"
            ]
    return help_lines