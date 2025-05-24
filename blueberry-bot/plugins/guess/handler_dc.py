from nonebot import on_command,logger
from nonebot.rule import is_type
from nonebot.internal.adapter.bot import Bot

from nonebot.adapters.discord import MessageEvent
from nonebot.adapters import Message
from nonebot.params import CommandArg


from .handler_base import INSTANCES,guess_command

def main():
    handler_cmd = on_command("guess",is_type(MessageEvent))
    @handler_cmd.handle()
    async def _(bot:Bot,event:MessageEvent,args: Message = CommandArg()):
        manager=INSTANCES.getOrCreateGuessManager(f"dc_{event.channel_id}")
        
        message=args.extract_plain_text().strip()
        logger.debug(f"'{message}' from{event}")
        feedBackMessage = guess_command(message,manager)
        if(feedBackMessage):
            await handler_cmd.send(feedBackMessage.replace("{username}","@"+event.author.username))
        pass