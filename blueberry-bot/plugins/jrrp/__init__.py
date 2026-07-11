import datetime
import io
import math
import random
import time
from nonebot import on_command,logger,get_plugin_config,get_loaded_plugins,get_driver,require
from nonebot.rule import is_type
from nonebot.internal.adapter import Bot,Event,Message
from nonebot.params import CommandArg
import cv2
import numpy as np

require("bbot_api")
from ..bbot_api import TextImageMessage

jrrp = on_command("jrrp")
@jrrp.handle()
async def _(bot:Bot,event:Event,args:Message=CommandArg()):
    
    value=random.Random((datetime.date.today().toordinal())+hash(event.get_user_id())).randint(0,100)
    reply=[]
    reply.append(f"你的今日人品是: {value}")
    if value>=100:
        reply.append("完美!")
    elif value>=97:
        reply.append("就差一点点...")
    elif value>=90:
        reply.append("运气不错哦!")
    elif value<20:
        reply.append("没事, 这只是个数字...")
    elif value==50:
        reply.append("刚好一半. 完美的平衡.")
    else:
        reply.append("今天也要开开心心喵")
    
    await jrrp.send("\n".join(reply))
    
randint_cmd = on_command("randint")
@randint_cmd.handle()
async def _(bot:Bot,event:Event,args:Message=CommandArg()):
    argv=args.extract_plain_text().split()
    v1=0
    v2=100
    try:
        if len(argv)>=1:
            v1=int(argv[0])
        if len(argv)>=2:
            v2=int(argv[1])
    except:
        await randint_cmd.finish(f"用法: randint [X] [Y]"
                                 +"\n默认: 0 100")
        
    vmin=min(v1,v2)
    vmax=max(v1,v2)
    
    await randint_cmd.send(f"随机结果: randint({vmin},{vmax}) -> {random.randint(vmin,vmax)}")
    
randcolor = on_command("randcolor")
@randcolor.handle()
async def _(bot:Bot,event:Event,args:Message=CommandArg()):
    color=random.randint(0,0xFFFFFF)
    
    # 用 OpenCV 生成纯色图片
    b = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    r = color & 0xFF
    img = np.full((128, 128, 3), (b, g, r), dtype=np.uint8)
    buf = io.BytesIO()
    buf.write(cv2.imencode(".png", img)[1].tobytes())
    img_bytes = buf.getvalue()
    
    msg = TextImageMessage.build(bot)
    msg.addText(f"随机结果: #{color:06X}")
    msg.addImage(img_bytes)
    
    await msg.send(randcolor)
    
def get_help(bot:Bot,event:Event):
    return [
        "jrrp 获取今日人品(运气)",
        "randcolor 随机颜色",
        "randint [X] [Y] 随机抽个X和Y之间的整数"
    ]