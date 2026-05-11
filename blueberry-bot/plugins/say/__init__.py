from typing import Type
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Bot,Message,Event
from nonebot.adapters.onebot.v11 import MessageSegment as OBMessageSegment,GroupMessageEvent as OBGroupMessageEvent, Bot as OBBot
from nonebot.adapters.discord import MessageEvent as DCMessageEvent, Bot as DCBot, MessageSegment as DCMessageSegment
from nonebot.params import CommandArg
from nonebot import on_command,logger
from nonebot.permission import SUPERUSER
from nonebot import require,get_driver
from nonebot.matcher import Matcher
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
    default_enabled:bool=False
    config_path:str|None=None
    def __init__(self,config_path:str|None=None) -> None:
        self.config_path=config_path
    def set_enabled(self, id:str, enable:bool):
        self.allowed_sessions[id]=enable
    def is_enabled(self, id:str):
        return self.allowed_sessions.get(id) if self.allowed_sessions.keys().__contains__(id) else self.default_enabled
    def save(self):
        if not self.config_path:
            return
        with open(self.config_path,"w") as f:
            json.dump({"allowed_sessions":self.allowed_sessions,"default_enabled":self.default_enabled},f)
    def load(self):
        if not self.config_path or not os.path.exists(self.config_path):
            return
        with open(self.config_path,"r") as f:
            data=json.load(f)
            if isinstance(data,dict):
                raw_sessions = data.get("allowed_sessions", self.allowed_sessions)
                self.allowed_sessions = {}
                for k, v in raw_sessions.items():
                    self.allowed_sessions[migrate_id_key(k)] = v
                self.default_enabled=data.get("default_enabled",self.default_enabled)

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
async def _(event:Event, arg: Message = CommandArg()):
    await set_say_state(True,arg.extract_plain_text().strip()=="-a",event,say_on)

@say_off.handle()
async def _(event:Event, arg: Message = CommandArg()):
    await set_say_state(False,arg.extract_plain_text().strip()=="-a",event,say_off)
        
async def set_say_state(enable:bool, isall:bool, event:Event, matcher:Type[Matcher]):
    if isall:
        say_config.default_enabled=enable
        await matcher.finish(f"say功能已默认{'启用' if enable else '关闭'}！")
    else:
        say_config.set_enabled(getid(event),enable)
        await matcher.finish(f"say功能已为本会话{'启用' if enable else '关闭'}！")


def migrate_id_key(key: str) -> str:
    """自动迁移旧格式 ID key 到当前格式（带下划线）。
    
    旧格式: dc<id> / group<id> / mc<name> / u<id>
    当前格式: dc_<id> / group_<id> / mc_<name> / u_<id>
    """
    if key.startswith("dc") and not key.startswith("dc_"):
        return "dc_" + key[2:]
    if key.startswith("group") and not key.startswith("group_"):
        return "group_" + key[5:]
    if key.startswith("mc") and not key.startswith("mc_"):
        return "mc_" + key[2:]
    if key.startswith("u") and not key.startswith("u_"):
        return "u_" + key[1:]
    return key
