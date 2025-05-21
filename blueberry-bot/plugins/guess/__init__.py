from nonebot import on_startswith,on_command,on_type
from nonebot.rule import startswith
from nonebot.internal.adapter.event import Event
from nonebot.internal.adapter.bot import Bot
from nonebot.adapters.minecraft import Bot as MCBot
from nonebot.adapters.minecraft import Event as MCEvent
from nonebot.adapters.minecraft import BaseChatEvent
from . import guess_core,guess_data
import nonebot

guess_data.load_all_data()
loadEntityCats=[]
for value in guess_data.ENTITY_MANAGER.category_data.values():
    loadEntityCats.append(f"{value.id}={value.name}")
    
print(f"已加载实体类别: {", ".join(loadEntityCats)}")
print(f"已加载地图: {", ".join(guess_data.MAP_MANAGER.map_data.keys())}")

handler_1 = on_startswith("&")
@handler_1.handle()
async def _(bot:Bot,event:Event):
    print(event)
    message = await run_command(str(event.get_message()).removeprefix("&").strip())
    if(message):
        await handler_1.send(message)
    pass


guess_manager_mc=guess_core.GuessManager()

async def run_command(cmd:str)->str|None:
    if cmd.startswith("guess"):
        return guess_command(cmd.removeprefix("guess").strip(),guess_manager_mc)

def guess_command(cmd:str,manager:guess_core.GuessManager)->str|None:
    if cmd.startswith("start"):
        return manager.start()
    elif cmd.startswith("giveup"):
        return manager.cancel()
    else:
        return manager.do_guess(cmd)