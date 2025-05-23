from nonebot import on_startswith
from nonebot.rule import is_type
from nonebot.internal.adapter.bot import Bot
from nonebot.adapters.minecraft import BaseChatEvent

from .handler_base import GuessManagerInstances,run_command,INSTANCES


def main():
    handler_msg = on_startswith("&",is_type(BaseChatEvent))
    @handler_msg.handle()
    async def _(bot:Bot,event:BaseChatEvent):
        manager=INSTANCES.getOrCreateGuessManager("mc_"+event.server_name)
        message=event.get_message().extract_plain_text()
        print(event)
        feedBackMessage = await run_command(str(message).removeprefix("&").strip(),manager)
        if(feedBackMessage):
            await handler_msg.send(feedBackMessage)
        pass
