from nonebot.adapters import Event
from nonebot.adapters.discord import GuildMessageCreateEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OBGroupMessageEvent

def getid(event: Event) -> str:
    if isinstance(event,GuildMessageCreateEvent):
        return "dc"+str(event.guild_id)
    if isinstance(event,OBGroupMessageEvent):
        return "group"+str(event.group_id)
    else:
        return "u" + str(event.get_user_id())