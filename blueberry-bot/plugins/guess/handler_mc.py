from nonebot import on_command,logger
from nonebot.rule import is_type
from nonebot.internal.adapter.bot import Bot
from nonebot.adapters.minecraft import BaseChatEvent
from nonebot.adapters import Message
from nonebot.params import CommandArg

from .handler_base import INSTANCES,guess_command


def main():
    handler_msg = on_command("guess",is_type(BaseChatEvent))
    @handler_msg.handle()
    async def _(bot:Bot,event:BaseChatEvent,args: Message = CommandArg()):
        manager=INSTANCES.getOrCreateGuessManager("mc_"+event.server_name)
        
        message=args.extract_plain_text().strip()
        logger.debug(f"'{message}' from{event}")
        feedBackMessage = guess_command(message,manager)
        if(feedBackMessage):
            await handler_msg.send("[§bBlueberry_Bot§r]"+feedBackMessage)
        pass
