from nonebot import require
require('bbot_api')
from ...bbot_api.message_compat import TextImageMessage
from ...bbot_api.message_compat.buttons import KBButton


require('bbot_render')
require('gd_api')

def add_page_buttons(page:int, reply:TextImageMessage, maxpages:int, cmd_no_page:str):
    reply.addLine("")
    if page>1:
        reply.addButton(KBButton(text=f"<<",command=f"{cmd_no_page} -p {1}"))
        reply.addButton(KBButton(text=f"<-",command=f"{cmd_no_page} -p {page-1}"))
    reply.addText(" ")
    if page<maxpages:
        reply.addButton(KBButton(text=f"->",command=f"{cmd_no_page} -p {page+1}"))
        reply.addButton(KBButton(text=f">>",command=f"{cmd_no_page} -p {maxpages}"))