from nonebot import on_startswith,on_command
from nonebot.rule import is_type
from nonebot.internal.adapter.bot import Bot

from nonebot.adapters.discord import MessageEvent


from .handler_base import GuessManagerInstances,run_command,INSTANCES

def main():
    handler_msg = on_startswith("&",is_type(MessageEvent))
    @handler_msg.handle()
    async def _(bot:Bot,event:MessageEvent):
        manager=INSTANCES.getOrCreateGuessManager(f"dc_{event.channel_id}")
        message=event.get_message().extract_plain_text()
        print(event)
        feedBackMessage = await run_command(message.removeprefix("&").strip(),manager)
        if(feedBackMessage):
            await handler_msg.send(feedBackMessage)
        pass


    handler_cmd = on_command("guess",is_type(MessageEvent))
    @handler_cmd.handle()
    async def _(bot:Bot,event:MessageEvent):
        manager=INSTANCES.getOrCreateGuessManager(f"dc_{event.channel_id}")
        message=event.get_message().extract_plain_text()
        print(event)
        feedBackMessage = await run_command(message.removeprefix("/").strip(),manager)
        if(feedBackMessage):
            await handler_cmd.send(feedBackMessage)
        pass