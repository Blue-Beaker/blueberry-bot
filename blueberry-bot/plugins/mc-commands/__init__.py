import json
from nonebot import on_command,logger,on_startswith
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot
from nonebot.adapters.minecraft import BaseChatEvent,MessageEvent
from nonebot.adapters import Message
from nonebot.params import CommandArg

CONFIG_PATH="config.json"

# server_prefixes:dict[str,str]={}
# ops:list[str]=[]

# with open(CONFIG_PATH,"r") as f:
#     configFile:dict=json.load(f)
#     ops=configFile.get("ops",[])
#     server_prefixes=configFile.get("prefixes",{})

# logger.info(f"loaded config: ops={ops},server_prefixes={server_prefixes}")

# def convert_server_command(cmd:str,bot1:Bot,bot2:Bot):
#     prefix1=server_prefixes.get(bot1.self_id,"")
#     prefix2=server_prefixes.get(bot2.self_id,"")
#     return cmd.replace(prefix1,prefix2)

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
        await bot.send_msg(message=e.__str__())
        await bot.send_msg(message=commandToSend)
    # bot.send_private_msg(uuid=event.player.uuid,nickname=event.player.nickname,message=f"[§bBlueberry_Bot§r] 来自{name}服务器: \n{msg}")