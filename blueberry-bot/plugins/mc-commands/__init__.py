import json
import traceback
from nonebot import on_command,logger,on_startswith,get_plugin_config
from nonebot.rule import is_type
from nonebot.adapters.minecraft.bot import Bot
from nonebot.adapters.minecraft import BaseChatEvent,MessageEvent
from nonebot.adapters.minecraft import Message as MCMessage
from nonebot.adapters.minecraft import MessageSegment as MCMessageSegment
from nonebot.adapters.minecraft.model import ClickEvent,HoverEvent,ClickAction,HoverAction,BaseComponent
from nonebot.adapters import Message
from nonebot.params import CommandArg

from config import Config

plugin_config = get_plugin_config(Config)

def is_command_segment_number(arg:str):
    for i in arg:
        if i not in "0123456789.-~":
            return False
    return True
class TpCommandBuilder:
    def __init__(self) -> None:
        self.target:str|None=None
        self.destination:str|None=None
        self.x:str|None=None
        self.y:str|None=None
        self.z:str|None=None
        self.yaw:str|None=None
        self.pitch:str|None=None
        self.dim:str|None=None
    @classmethod
    def fromArgs(cls,rawargs:list[str]):
        inst=cls()
        args=rawargs.copy()
        
        if(len(args)<=2):
            # first param [target]
            if(len(args)==2):
                inst.target=args[0]
            # tpx [player] [dimension]
            if(is_command_segment_number(args[-1])):
                inst.dim=args[-1]
            # tpx [player] [destination]
            else:
                inst.destination=args[-1]
        else:
            if(not is_command_segment_number(args[0])):
                inst.target=args.pop(0)
                
            inst.x,inst.y,inst.z=args[0:3]
            if(args.__len__()==4 or args.__len__()==6):
                inst.dim=args.pop(3)
            if(args.__len__()>=5):
                inst.yaw,inst.pitch=args[3:5]
                
        return inst
    def build(self):
        params=[]
        if(self.target):
            params.append(self.target)
        if(self.destination):
            params.append(self.destination)
        elif(self.x):
            params.extend((self.x,self.y,self.z))
            if(self.dim):
                params.append(self.dim)
            if(self.yaw):
                params.extend((self.yaw,self.pitch))
        elif(self.dim):
            params.extend(self.dim)
        if self.dim:
            return f"tpx {" ".join(params)}"
        return f"tp {" ".join(params)}"
    
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
    cmd=TpCommandBuilder.fromArgs(argsStrs)
    if(not cmd):
        await bot.send_private_msg(message="用法: /tp [target player] <destination player> OR /tp [target player] <x> <y> <z> [<yaw> <pitch>]")
        return
        
    cmd.target=playername
    commandToSend="execute "+playername+" ~ ~ ~ "+cmd.build()
    # if len(argsStrs)==2 or len(argsStrs)==4 or len(argsStrs)==4:
    #     argsStrs.pop(0)
    # argsStrs.insert(0,playername)
    
    # commandToSend=f"tp {" ".join(argsStrs)}"
    try:
        logger.info("sending command: "+commandToSend)
        msg,result = await bot.send_rcon_cmd(command=commandToSend)
    except Exception as e:
        await bot.send_msg(message="\n".join(traceback.format_exception_only(e)))
        logger.error(traceback.format_exc())
        await bot.send_msg(message=commandToSend)
    # bot.send_private_msg(uuid=event.player.uuid,nickname=event.player.nickname,message=f"来自{name}服务器: \n{msg}")

class Waypoint:
    def __init__(self):
        self.name:str
        self.icon:str
        self.x:str
        self.y:str
        self.z:str
        self.color:str
        self.dimension:str
    @classmethod
    def from_message(cls,msg:str):
        inst=cls()
        spl=msg.split(":")
        if(spl.__len__()<10):
            return None
        inst.name=spl[1]
        inst.icon=spl[2]
        inst.x=spl[3]
        inst.y=spl[4]
        inst.z=spl[5]
        inst.color=spl[6]
        inst.dimension=spl[8]
        return inst
        
waypoint_msg = on_startswith("xaero-waypoint")
@waypoint_msg.handle()
async def _(bot:Bot,event:BaseChatEvent):
    
    "xaero-waypoint:new-home:H:-27:72:-438:14:false:0:Internal-overworld-waypoints"
    msg=event.message.extract_plain_text()
    waypoint=Waypoint.from_message(msg)
    if(waypoint):
        tpCommand=f"-tpx {waypoint.x} {waypoint.y} {waypoint.z} {waypoint.dimension}"
        sendmsg=MCMessage()
        sendmsg.append(MCMessageSegment.text(
            text=f"点此传送: {waypoint.name}",
            click_event=ClickEvent(action=ClickAction.SUGGEST_COMMAND,
                                   value=tpCommand),
            hover_event=HoverEvent(action=HoverAction.SHOW_TEXT,
                                   text=[BaseComponent(text=tpCommand)])))
        
        await bot.send_msg(message=sendmsg)


