from enum import Enum
from nonebot import logger, on_command,get_loaded_plugins,require
from nonebot.message import run_preprocessor
from nonebot.adapters import Bot,Event,Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import CommandRule
from nonebot.matcher import Matcher
from nonebot.exception import IgnoredException,MatcherException
from .utils import get_matcher_references,is_permission_manageable
from .manager import CommandPermManager,CommandPermEntry

require("bbot_api")
from ..bbot_api.argparse import ArgParser

list_commands = on_command("cmd-list",permission=SUPERUSER)
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
            "列出所有命令规则:",
            "cmd-perms list",
            "列出所选命令规则链:",
            "cmd-perms get <command>",
            "在所选命令规则链中index位置(或末尾)加入/删除规则:",
            "cmd-perms add <command> <group>=<enabled> [index]",
            "cmd-perms remove <command> [index]",
            "清除所选命令规则链:",
            "cmd-perms clear <command>",
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
            reply.append("当前绑定规则的命令:")
            for i in MANAGER.entries.values():
                reply.append(format_rules(i))
            await finish()
            return
            
        if args.__len__()<2:
            await finish("缺少 command 参数")
            return
            
        cmd_id = args[1]
        if action==PermsCmdAction.GET:
            rule = MANAGER.get_rule(cmd_id)
            await finish(format_get_rules(cmd_id))
            return
        elif action==PermsCmdAction.CLEAR:
            rule = MANAGER.get_rule(cmd_id)
            await finish("暂未实现")
            return
            
        if action==PermsCmdAction.INSERT:
            if args.__len__()<3:
                await finish("缺少 rule 参数")
                return
            rule = args[2]
            index = int(args[3]) if args.__len__()>=4 else None
            rule1 = CommandPermEntry.parse_rule(rule)
            if not rule1:
                await finish(f"解析失败:{rule}")
                return
            MANAGER.add_rule(cmd_id,rule1[0],rule1[1],index)
            reply.append(f"已添加规则:{rule1}")
            await finish(format_get_rules(cmd_id))
            
        elif action==PermsCmdAction.REMOVE:
            index = int(args[2]) if args.__len__()>=3 else None
            MANAGER.remove_rule(cmd_id,index)
            reply.append(f"已移除规则")
            await finish(format_get_rules(cmd_id))
        
    except Exception as e:
        if isinstance(e,MatcherException):
            raise e
        await cmd_perms.send(f"错误: {e}")
        
def format_get_rules(cmd_id:str):
    rule = MANAGER.get_rule(cmd_id)
    if rule:
        return format_rules(rule)
    else:
        return f"{cmd_id} 没有绑定规则"
    
def format_rules(entry:CommandPermEntry|None):
    lines:list[str]=[]
    if not entry:
        return ""
    lines.append(f"{entry.cmd_id}:")
    for group,enable in entry.rule_chain:
        lines.append(f"  {group}={enable}")
    return "\n".join(lines)

MANAGER = CommandPermManager()

# MANAGER.add_entry(CommandPermEntry("jrrp:jrrp").add_rule("global",False).add_rule("verified",True))

@run_preprocessor
async def _(bot:Bot, event: Event, matcher: Matcher):
    checked = MANAGER.check_permission(matcher,bot,event)
    # logger.info(f"{matcher} {checked}")
    if not checked:
        await matcher.send("此会话未启用此命令")
        raise IgnoredException(f"No permission: {bot} {event} {matcher}")