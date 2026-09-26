from enum import Enum
from nonebot import logger, on_command,get_loaded_plugins,require,get_driver
from nonebot.message import run_preprocessor
from nonebot.adapters import Bot,Event,Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import CommandRule
from nonebot.matcher import Matcher
from nonebot.exception import IgnoredException,MatcherException
from .utils import format_matcher_references,is_permission_manageable,get_all_matchers,get_matcher_references,MatcherReference
from .manager import CommandPermManager,CommandPermEntry,PermAction

require("bbot_api")
from ..bbot_api.argparse import ArgParser

require("bbot_help")
from ..bbot_help import SUPERUSER_HELP_REGISTRY

driver = get_driver()
@driver.on_startup
async def _():
    MANAGER.load()
    MANAGER.save()
    
@driver.on_shutdown
async def _():
    MANAGER.save()

list_commands = on_command("cmd-list",permission=SUPERUSER)
@list_commands.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    args=msg.extract_plain_text()
    
    reply:list[str]=[]
    for plugin in get_loaded_plugins():
        for matcher in plugin.matcher:
            if not is_permission_manageable(matcher):
                continue
            references = format_matcher_references(matcher)
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

class PermsCmdAction(Enum):
    LIST='list'
    GET='get'
    INSERT='add'
    REMOVE='remove'
    CLEAR='clear'

cmd_perms = on_command("cmd-perms",permission=SUPERUSER)
@cmd_perms.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    def get_help():
        return '\n'.join([
            "列出所有规则:",
            "cmd-perms list",
            "列出匹配所选命令的规则:",
            "cmd-perms get <command>",
            "在规则链中加入/删除规则:",
            "cmd-perms add <group> <commands> <action> [priority]",
            "删除所选位置的规则:",
            "cmd-perms remove <index>"
        ])
        
    args=msg.extract_plain_text().split()
    if not args:
        await cmd_perms.finish(get_help())
        
    reply:list[str]=[]
    async def finish(msg:str|None=None):
        if msg:
            reply.append(msg)
        await cmd_perms.finish("\n".join(reply))
    try:
        action = PermsCmdAction(args[0])
        if action==PermsCmdAction.LIST:
            reply.append("当前规则:")
            for i in MANAGER.entries:
                reply.append(format_rules(i))
            await finish()
            return
            
        if args.__len__()<2:
            await finish("缺少 command 参数")
            return
            
        arg1 = args[1]
        if action==PermsCmdAction.GET:
            spl1=arg1.split(":")
            mat:type[Matcher]|None=None
            mats = get_all_matchers(spl1[0])
            
            for key,m in mats.items():
                if key==arg1:
                    mat=m
                    break
            
            rules = MANAGER.get_command_rules(mat or MatcherReference(spl1[0],spl1[1]))
            
            references = get_matcher_references(mat) if mat else [MatcherReference(spl1[0],spl1[1])]
            reply.append(f"命令 [{references}] 受如下规则影响:")
            await finish('\n'.join([f"{r.priority} {r.dump_rule()}" for r in rules]))
            return
        elif action==PermsCmdAction.CLEAR:
            MANAGER.save()
            await finish("暂未实现")
            return
            
        if action==PermsCmdAction.INSERT:
            if args.__len__()<3:
                await finish("缺少 rule 参数")
                return
            rule = " ".join(args[1:])
            rule1 = CommandPermEntry.load_rule(rule)
            if not rule1:
                await finish(f"解析失败:{rule}")
                return
            MANAGER.add_entry(rule1)
            MANAGER.save()
            reply.append(f"已添加规则:")
            await finish(rule1.dump_rule())
            
        elif action==PermsCmdAction.REMOVE:
            index = int(arg1) if args.__len__()>=2 else None
            removed=MANAGER.remove_rule(index)
            MANAGER.save()
            reply.append(f"已移除规则")
            await finish(removed.dump_rule())
        
    except Exception as e:
        if isinstance(e,MatcherException):
            raise e
        await cmd_perms.send(f"错误: {e}")
    
def format_rules(entry:CommandPermEntry|None):
    lines:list[str]=[]
    if not entry:
        return ""
    lines.append(entry.dump_rule())
    return "\n".join(lines)

MANAGER = CommandPermManager("config/command_perms.json")

# MANAGER.add_entry(CommandPermEntry("jrrp:jrrp").add_rule("global",False).add_rule("verified",True))

@run_preprocessor
async def _(bot:Bot, event: Event, matcher: Matcher):
    is_superuser = SUPERUSER(bot,event)
    
    checked = MANAGER.check_permission(matcher,bot,event)
    # logger.info(f"{matcher} {checked}")
    if checked != PermAction.ALLOW:
        if checked == PermAction.DENY:
            await matcher.send("此会话未启用此命令")
            
        if SUPERUSER(bot,event):
            return
        raise IgnoredException(f"No permission: {bot} {event} {matcher}")
    
@SUPERUSER_HELP_REGISTRY.addHelpFunc
def _():
    return ["cmd-list 列出命令列表","cmd-perms 管理命令权限"]