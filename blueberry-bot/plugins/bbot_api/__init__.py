from pathlib import Path
from nonebot.adapters import Event
from nonebot.adapters.discord import GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent,Bot as OBBot

def getid(event: Event) -> str:
    if isinstance(event,GuildMessageCreateEvent):
        return "dc"+str(event.guild_id)
    if isinstance(event,OBGroupMessageEvent):
        return "group"+str(event.group_id)
    else:
        return "u" + str(event.get_user_id())
    
async def reaction_emoji(bot:OBBot,msg:int,emoji:int):
    data={
    "message_id": msg,
    "emoji_id": str(emoji),
    "set": True
    }
    await bot.call_api("set_msg_emoji_like",**data)
    
def loadFile(file:str|Path) -> bytes:
    with open(file,'rb') as f:
        return f.read()