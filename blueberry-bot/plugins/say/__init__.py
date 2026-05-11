from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Bot,Message,Event
from nonebot.adapters.onebot.v11 import MessageSegment as OBMessageSegment,GroupMessageEvent as OBGroupMessageEvent, Bot as OBBot
from nonebot.adapters.discord import MessageEvent as DCMessageEvent, Bot as DCBot, MessageSegment as DCMessageSegment
from nonebot.params import CommandArg
from nonebot import on_command,logger
from nonebot.permission import SUPERUSER
from nonebot import require,get_driver
import requests
from pathlib import Path
import os,json

from .config import Config

require("bbot_api")
from ..bbot_api import getid

__plugin_meta__ = PluginMetadata(
    name="say",
    description="",
    usage="",
    config=Config,
)

def json_group_audio(group_id: int, path: str) -> dict:
    return {
        'group_id': group_id,
        'message': [{
            'type': 'record',
            'data': {
                'file': path
                    }
        }]}

def json_private_audio(user_id: int, path: str) -> dict:
    return {
        'user_id': user_id,
        'message': [{
            'type': 'record',
            'data': {
                'file': path
                    }
        }]}

plugin_config = get_plugin_config(Config)

say = on_command("say")
say_on = on_command("say_on",permission=SUPERUSER)
say_off = on_command("say_off",permission=SUPERUSER)

driver=get_driver()

CONFIG_FILE="say_config.json"

@driver.on_startup
async def load():
    say_config.load()
    
@driver.on_shutdown
async def save():
    say_config.save()


class SayConfig:
    allowed_sessions:dict[str,bool]={}
    config_path:str|None=None
    def __init__(self,config_path:str|None=None) -> None:
        self.config_path=config_path
    def set_enabled(self, id:str, enable:bool):
        self.allowed_sessions[id]=enable
    def is_enabled(self, id:str):
        return self.allowed_sessions.get(id,False)
    def save(self):
        if not self.config_path:
            return
        with open(self.config_path,"w") as f:
            json.dump({"allowed_sessions":self.allowed_sessions},f)
    def load(self):
        if not self.config_path or not os.path.exists(self.config_path):
            return
        with open(self.config_path,"r") as f:
            data=json.load(f)
            if isinstance(data,dict):
                self.allowed_sessions=data.get("allowed_sessions",self.allowed_sessions)

say_config = SayConfig(CONFIG_FILE)
    
@say.handle()
async def _(bot:Bot,event: Event, arg: Message = CommandArg()):
    if not say_config.is_enabled(getid(event)):
        await say.finish("say功能目前不开放哦QAQ")
    text = str(arg)
    if len(text) == 0:
        await say.finish("你得在say后面加点东西……")
    if len(text) > 1000:
        await say.finish("请善待小小卒！")
    res = requests.get(plugin_config.say_request_url.replace("{$text}",text))
    if res.status_code != 200:
        logger.error(f"Request say failed: {res.status_code}")
        await say.finish()
        
    content_disposition = res.headers.get('Content-Disposition')

    if content_disposition:
        # 解析文件名
        file_name = content_disposition.split('filename=')[1]
        file_name = file_name.strip('\'"')
    else:
        file_name = "say.wav"
    if isinstance(bot,OBBot):
        await say.send(OBMessageSegment.record(res.content))
    elif isinstance(bot,DCBot):
        await say.send(DCMessageSegment.attachment(file_name,None,res.content))
        
    await say.finish()

@say_on.handle()
async def _(event:Event):
    say_config.set_enabled(getid(event),True)
    await say_on.finish("say功能已为本会话启用！")

@say_off.handle()
async def _(event:Event):
    say_config.set_enabled(getid(event),False)
    await say_off.finish("say功能已为本会话关闭！")
