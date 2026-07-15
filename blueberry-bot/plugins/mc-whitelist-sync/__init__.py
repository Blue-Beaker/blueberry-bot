import json
from nonebot import on_command,logger,on_startswith,get_plugin_config,get_adapter
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot
from nonebot.adapters.minecraft import BasePlayerCommandEvent,MessageEvent,Adapter as MCAdapter
from nonebot.adapters import Message,Bot as BaseBot, Event as BaseEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

CONFIG_PATH="config.json"

from .config import Config

plugin_config = get_plugin_config(Config)

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
    if((bot.self_id not in server_prefixes.keys())or not( event.player.is_op or str(event.player.uuid) in ops)):
        return
    for name,bot2 in bot.adapter.bots.items():
        if(bot==bot2 or not isinstance(bot2,Bot) or bot2.self_id not in server_prefixes.keys()):
            continue
        msg,result = await bot2.send_rcon_cmd(command=convert_server_command(cmd,bot,bot2))
        if(result>=1):
            await bot.send_private_msg(uuid=event.player.uuid,nickname=event.player.nickname,message=f"来自{name}服务器: \n{msg}")
            
whitelist_msg=on_command("mc-whitelist",permission=SUPERUSER)
@whitelist_msg.handle()
async def _(bot:BaseBot,event:BaseEvent,args:Message=CommandArg()):
    reply=[]
    mc_adapter = get_adapter(MCAdapter)
    for name,bot2 in mc_adapter.bots.items():
        if(bot==bot2 or not isinstance(bot2,Bot) or bot2.self_id not in server_prefixes.keys()):
            continue
        msg,result = await bot2.send_rcon_cmd(command=server_prefixes[bot2.self_id]+" "+args.extract_plain_text().strip())
        # if(result>=1):
        reply.append(f"来自{name}服务器: \n{msg}")
        
    await whitelist_msg.send("\n".join(reply))
    
mcexec=on_command("mc-exec",permission=SUPERUSER)
@mcexec.handle()
async def _(bot:BaseBot,event:BaseEvent,args:Message=CommandArg()):
    cmdargs=args.extract_plain_text().split()
    
    mc_adapter = get_adapter(MCAdapter)
    if not cmdargs:
        await mcexec.finish("用法: mc-exec <服务器> <命令...>"
                            +"\n当前服务器列表: \n"
                            +", ".join(mc_adapter.bots.keys()))
        
    server_name=cmdargs[0]
    
    
    mc_bot=mc_adapter.bots.get(server_name,None)
    
    if not mc_bot:
        for name,bot2 in mc_adapter.bots.items():
            if bot2.self_id.lower()==server_name.lower():
                mc_bot=bot2
                break
    
    if not mc_bot:
        await mcexec.finish("未知服务器. 当前服务器列表:\n"+", ".join(mc_adapter.bots.keys()))
    
    assert isinstance(mc_bot,Bot)
    msg,result = await mc_bot.send_rcon_cmd(command=" ".join(cmdargs[1:]))
    await mcexec.finish(f"来自服务器的消息: {msg}\n (返回值={result})")