import json
from nonebot import on_command,logger,on_startswith,get_plugin_config
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot
from nonebot.adapters.minecraft import BaseChatEvent,MessageEvent
from nonebot.adapters import Message
from nonebot.params import CommandArg

from config import Config

plugin_config = get_plugin_config(Config)

handler_msg = on_command("tp")
@handler_msg.handle()
async def _(bot:Bot,event:BaseChatEvent,args: Message = CommandArg()):
    cmd=event.message.extract_plain_text()
    logger.info(cmd,event.player.uuid.__str__())
    playername=event.player.nickname
    # if((bot.self_id not in server_prefixes.keys())or not( event.player.is_op or str(event.player.uuid) in ops)):
    #     return
    
    argsStrs=[str(arg) for arg in str(args).split(" ")]
    # print(argsStrs)
    
    if len(argsStrs)==2 or len(argsStrs)==4 or len(argsStrs)==4:
        argsStrs.pop(0)
    argsStrs.insert(0,playername)
    
    commandToSend=f"tp {" ".join(argsStrs)}"
    try:
        logger.info("sending command: "+commandToSend)
        msg,result = await bot.send_rcon_cmd(command=commandToSend)
    except Exception as e:
        await bot.send_msg(message=plugin_config.mc_message_prefix+e.__str__())
        await bot.send_msg(message=plugin_config.mc_message_prefix+commandToSend)
    # bot.send_private_msg(uuid=event.player.uuid,nickname=event.player.nickname,message=f"[§bBlueberry_Bot§r] 来自{name}服务器: \n{msg}")