from nonebot import logger, on_command,get_loaded_plugins
from nonebot.message import run_preprocessor
from nonebot.adapters import Bot,Event,Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import CommandRule
from nonebot.matcher import Matcher
from nonebot.exception import IgnoredException
from .utils import get_matcher_references,is_permission_manageable
from .manager import CommandPermManager,CommandPermEntry

list_commands = on_command("list-commands",permission=SUPERUSER)
@list_commands.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    args=msg.extract_plain_text()
    
    reply:list[str]=[]
    for plugin in get_loaded_plugins():
        for matcher in plugin.matcher:
            if not is_permission_manageable(matcher):
                continue
            references = get_matcher_references(matcher)
            if args:
                matched=False
                for r in references:
                    if args in r:
                        matched=True
                        break
                if not matched:
                    continue
            if references:
                reply.append(','.join(references))
    await list_commands.finish("\n".join(reply))
    pass

MANAGER = CommandPermManager()

# MANAGER.add_entry(CommandPermEntry("jrrp:jrrp").add_rule("global",False).add_rule("verified",True))

@run_preprocessor
async def _(bot:Bot, event: Event, matcher: Matcher):
    checked = MANAGER.check_permission(matcher,bot,event)
    # logger.info(f"{matcher} {checked}")
    if not checked:
        await matcher.send("此会话未启用此命令")
        raise IgnoredException(f"No permission: {bot} {event} {matcher}")