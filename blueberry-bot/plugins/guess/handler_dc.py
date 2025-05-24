from nonebot import on_command,logger
from nonebot.rule import is_type
# from nonebot.internal.adapter.bot import Bot

from nonebot.adapters.discord import MessageEvent, Bot, MessageEvent, MessageSegment, Message
# from nonebot.adapters import Message
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
            split=feedBackMessage.split("{username}")
            msgseg=split[0]
            for segment in split[1:]:
                msgseg=msgseg+MessageSegment.mention_user(event.user_id)+MessageSegment.text(segment)
            
            await handler_cmd.send(msgseg)
        pass