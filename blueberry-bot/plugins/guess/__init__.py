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
    session=manager.get_session()
    if cmd.startswith("start"):
        if(session):
            return "当前有正在进行的guess 请先猜出来"
        feedback=manager.start_guess().reveal_info()
        return feedback
    elif cmd.startswith("giveup"):
        if(not session):
            return "当前有正在进行的guess 请先猜出来"
        manager.session=None
        return f"你放弃了! 答案是: {session.map_name}"
    else:
        if(not session):
            return "当前没有正在进行的guess 请&guess start开始猜图"
        return session.do_guess(cmd)