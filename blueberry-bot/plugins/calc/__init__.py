from nonebot import on_command,logger,get_plugin_config,get_loaded_plugins,get_driver,require
from nonebot.rule import is_type
from nonebot.internal.adapter import Bot,Event,Message
from nonebot.params import CommandArg
from nonebot.adapters.minecraft.bot import Bot as MCBot
from nonebot.permission import SUPERUSER

require("bbot_help")
from ..bbot_help import HELP_REGISTRY

try:
    import sympy
    from sympy.core import Expr
except:
    logger.error("Sympy not found. Calc will be disabled.")
    sympy=None

calc = on_command("calc")
@calc.handle()
async def _(bot:Bot,event:Event,msg:Message=CommandArg()):
    if not sympy:
        return
    
    reply:list[str]=[]
    try:
        expr=msg.extract_plain_text().strip()
        
        reply.append(expr)
        
        result:Expr=sympy.simplify(expr,evaluate=True)
        if str(expr)!=str(result):
            reply.append(f" = {result}")
            
        num=result.evalf()
        reply.append(f"-> {num}")
            
    except Exception as e:
        await calc.finish(f"错误: {e}")
        return
        
    await calc.finish("\n".join(reply))
    
@HELP_REGISTRY.addHelpFunc
def _():
    if not sympy:
        return
    return "calc <算式> 执行数学计算"
    