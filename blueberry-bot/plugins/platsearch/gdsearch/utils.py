from typing import Callable
from nonebot import require
require('bbot_api')
from ...bbot_api.message_compat import TextImageMessage
from ...bbot_api.message_compat.buttons import KBButton


require('bbot_render')
require('gd_api')

def add_page_buttons(page:int, reply:TextImageMessage, first_page:int, last_page:int, cmd_from_page:Callable[[int],str]):
    reply.addLine("")
    if page>first_page:
        reply.addButton(KBButton(text=f"<<",command=cmd_from_page(first_page)))
        reply.addButton(KBButton(text=f"<-",command=cmd_from_page(page-1)))
    reply.addText(" ")
    if page<last_page:
        reply.addButton(KBButton(text=f"->",command=cmd_from_page(page+1)))
        reply.addButton(KBButton(text=f">>",command=cmd_from_page(last_page)))