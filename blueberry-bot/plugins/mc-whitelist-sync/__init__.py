import json
from nonebot import on_command,logger,on_startswith
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot
from nonebot.adapters.minecraft import BasePlayerCommandEvent,MessageEvent
from nonebot.adapters import Message
from nonebot.params import CommandArg

CONFIG_PATH="config.json"

server_prefixes:dict[str,str]={}
ops:list[str]=[]

with open(CONFIG_PATH,"r") as f:
    configFile:dict=json.load(f)
    ops=configFile.get("ops",[])
    server_prefixes=configFile.get("prefixes",{})

logger.info(f"loaded config: ops={ops},server_prefixes={server_prefixes}")

def convert_server_command(cmd:str,bot1:Bot,bot2:Bot):
    prefix1=server_prefixes.get(bot1.self_id,"")
    prefix2=server_prefixes.get(bot2.self_id,"")
    return cmd.replace(prefix1,prefix2)

handler_msg = on_startswith("whitelist",is_type(BasePlayerCommandEvent))
@handler_msg.handle()
async def _(bot:Bot,event:BasePlayerCommandEvent):
    cmd=event.message.extract_plain_text()
    logger.info(cmd,event.player.uuid.__str__())
    if(not event.player.is_op and not str(event.player.uuid) in ops):
        return
    for name,bot2 in bot.adapter.bots.items():
        if(bot==bot2 or not isinstance(bot2,Bot)):
            continue
        msg,result = await bot2.send_rcon_cmd(command=convert_server_command(cmd,bot,bot2))
        if(result>=1):
            await bot.send_private_msg(uuid=event.player.uuid,nickname=event.player.nickname,message=f"[§bBlueberry_Bot§r] 来自{name}服务器: \n{msg}")