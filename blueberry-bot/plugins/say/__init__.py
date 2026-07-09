import math
import shutil
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
from ..bbot_api import getid as getid_raw,get_group_id
from ..bbot_api.group_config import GroupConfig,ConfigItem,make_config_handler
from ..bbot_api.profile_link.events import on_link, LinkUserEvent, LinkGroupEvent, UnlinkUserEvent, UnlinkGroupEvent
from ..bbot_api import message_compat

def getid(event:Event):
    id=getid_raw(event)
    if id.startswith("u_"):
        return get_group_id(event)
    return id

try:
    require("orb_api")
    from .. import orb_api
except:
    orb_api=None

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

class SayConfigItem(ConfigItem):
    enabled:bool=False
    cost_factor:float=1.0

class SayConfig(GroupConfig[SayConfigItem]):
    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(SayConfigItem, config_path)
    
    def is_enabled(self,id:str):
        return self.get(id).enabled
    
    def set_enabled(self, id:str, enable:bool):
        self.set(id,enabled=enable)
        
    def get_default_enabled(self):
        return self.get("global").enabled
    def set_default_enabled(self,enable:bool):
        self.set("global",enabled=enable)
        
    default_enabled = property(fget=get_default_enabled,fset=set_default_enabled)
        
    
CONFIG_PATH=Path("config/")
CONFIG_PATH.mkdir(parents=True,exist_ok=True)

say_config = SayConfig((CONFIG_PATH/"say_config.json").__str__())

driver=get_driver()

CONFIG_FILE="say_config.json"

def migrate_config():
    say_config_old.load()
    say_config.load()
    
    for i in say_config_old.allowed_sessions:
        say_config.set_enabled(i,True)
        
    say_config.set("global",enabled=say_config_old.default_enabled)
    
    say_config.save()

@driver.on_startup
async def load():
    if os.path.isfile(CONFIG_FILE):
        migrate_config()
        shutil.move(CONFIG_FILE,CONFIG_FILE+".bak")
    
    say_config.load()    
    logger.info(f"Loaded {say_config.group_overrides.keys().__len__()} say config entries")
    
@driver.on_shutdown
async def save():
    # say_config.save()
    say_config.save()

# ── profile_link 事件监听器 ──────────────────────────

@on_link(LinkUserEvent)
def _say_on_link(event: LinkUserEvent):
    if say_config.merge_profile(event.profile_id, event.raw_id):
        logger.info(f"say: 已合并配置 {event.raw_id} → {event.profile_id}")

@on_link(UnlinkUserEvent)
def _say_on_unlink(event: UnlinkUserEvent):
    if say_config.unmerge_profile(event.profile_id, event.raw_id):
        logger.info(f"say: 已拆分配置 {event.profile_id} → {event.raw_id}")

@on_link(LinkGroupEvent)
def _say_on_link_group(event: LinkGroupEvent):
    if say_config.merge_profile(event.profile_id, event.raw_group_id):
        logger.info(f"say: 已合并群配置 {event.raw_group_id} → {event.profile_id}")

@on_link(UnlinkGroupEvent)
def _say_on_unlink_group(event: UnlinkGroupEvent):
    if say_config.unmerge_profile(event.profile_id, event.raw_group_id):
        logger.info(f"say: 已拆分群配置 {event.profile_id} → {event.raw_group_id}")

class SayConfigOld:
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

say_config_old = SayConfigOld(CONFIG_FILE)
    
@say.handle()
async def _(bot:Bot,event: Event, arg: Message = CommandArg()):
    event_id=getid(event)
    if not say_config.is_enabled(event_id):
        await say.finish("say功能目前不开放哦QAQ")
    text = str(arg)
    if len(text) == 0:
        await say.finish("你得在say后面加点东西……")
    if len(text) > 1000:
        await say.finish("请善待小小卒！")
    
    orb_cost=0
    orb_id=None
    if orb_api:
        orb_cost=math.ceil(max(len(text),10)*say_config.get(event_id).cost_factor)
        orb_id=orb_api.get_orb_owner_id(event)
        if orb_id:
            balance = orb_api.get_balance(orb_id)
            if balance < orb_cost:
                await say.finish(f"你的 Orbs 不足! 需要 {orb_cost}, 你只有 {balance}")
                
            orb_api.add_balance(orb_id,-orb_cost)
    
    res = requests.get(plugin_config.say_request_url.replace("{$text}",text))
    if res.status_code != 200:
        logger.error(f"Request say failed: {res.status_code}")
        
        if orb_api and orb_id:
            orb_api.add_balance(orb_id,-orb_cost)
            await say.finish("发生错误. 已退还消耗的 Orbs.")
            
        await say.finish("发生错误.")
        return
    
    content_disposition = res.headers.get('Content-Disposition')

    if content_disposition:
        # 解析文件名
        file_name = content_disposition.split('filename=')[1]
        file_name = file_name.strip('\'"')
    else:
        file_name = "say.wav"
        
    await say.send(message_compat.record(bot,res.content,file_name))
    
    # if isinstance(bot,OBBot):
    #     await say.send(OBMessageSegment.record(res.content))
    # elif isinstance(bot,DCBot):
    #     await say.send(DCMessageSegment.attachment(file_name,None,res.content))
        
    await say.finish()

@say_on.handle()
async def _(event:Event, arg: Message = CommandArg()):
    await set_say_state(True,arg.extract_plain_text().strip()=="-a",event,say_on)

@say_off.handle()
async def _(event:Event, arg: Message = CommandArg()):
    await set_say_state(False,arg.extract_plain_text().strip()=="-a",event,say_off)
        
gus_cfg=on_command("say-cfg",permission=SUPERUSER)
config_handler=make_config_handler("say-cfg",SayConfigItem,say_config,getid)
gus_cfg.handle()(config_handler)
        
async def set_say_state(enable:bool, isall:bool, event:Event, matcher:Type[Matcher]):
    if isall:
        say_config.default_enabled=enable
        await matcher.finish(f"say功能已默认{'启用' if enable else '关闭'}！")
    else:
        say_config.set_enabled(getid(event),enable)
        await matcher.finish(f"say功能已为本会话{'启用' if enable else '关闭'}！")
    say_config.save()


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

def get_help(bot:Bot,event:Event):
    if say_config.is_enabled(getid(event)):
        return "say 说一句话"
    else:
        return None