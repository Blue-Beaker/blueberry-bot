from typing import Type, cast
from nonebot.adapters import Bot
from nonebot.internal.adapter import Message
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment
from nonebot.adapters.qq.models import MessageKeyboard,InlineKeyboard,InlineKeyboardRow,Button,Action,RenderData
from nonebot.adapters.qq.message import Markdown
from urllib.parse import quote,unquote
from nonebot.matcher import Matcher

from ..buttons import ButtonKeyboard,KBButton
from .base import BaseTextImageMessage
from ..utils import escapeMarkdown

def convert_to_markdown(msg:Message|str):
    if isinstance(msg,Message):
        msg=msg.extract_plain_text()
    return QQMessage(QQMessageSegment.markdown(msg))

def build_keyboard(keyboard:ButtonKeyboard):
    ext_rows:list[InlineKeyboardRow]=[]
    for row in keyboard.rows:
        buttons:list[Button]=[]
        for b in row:
            buttons.append(Button(render_data=RenderData(label=b.text),action=Action(type=2,data=b.command)))
        ext_row=InlineKeyboardRow(buttons=buttons)
        ext_rows.append(ext_row)
    
    return MessageKeyboard(content=InlineKeyboard(rows=ext_rows))

def convert_button_md(button:KBButton):
    return f"""<qqbot-cmd-input text="{quote(button.command)}" show="{quote(button.text)}" reference="false" />"""

def build_keyboard_md(keyboard:ButtonKeyboard):
    lines:list[str]=[]
    for row in keyboard.rows:
        for b in row:
            lines.append(convert_button_md(b))
    return "\n".join(lines)

class QQTextImageMessage(BaseTextImageMessage[QQMessage]):
    def __init__(self) -> None:
        super().__init__(QQMessage(),QQBot)
        
    def convert_to_markdown(self):
        if self.markdown:
            return
        self.msg=convert_to_markdown(self.msg)
        
    @property
    def markdown(self):
        result = self.msg.get("markdown")
        return cast(Markdown,result[0]) if result.__len__()>0 else None
    
    @property
    def markdown_data(self):
        return self.markdown.data["markdown"] if self.markdown else None
        
    def addLine(self,text:str,markdown:bool=False):
        if self.msg.__len__()>0 and (self.markdown or self.msg[-1].is_text()):
            self.addText("\n")
        self.addText(text,markdown=markdown)
        return self
    def addText(self,text:str,markdown:bool=False):
        md_data=self.markdown_data
        if md_data:
            if md_data.content==None:
                md_data.content=""
            if not markdown:
                md_data.content+=escapeMarkdown(text)
            else:
                md_data.content+=text
        else:
            self.msg.append(text)
        return self
    
    def addImage(self,image:bytes,image_name:str="",small:bool=False):
        self.msg.append(QQMessageSegment.file_image(image,image_name))
        return self
    
    def addButtons(self,buttons:ButtonKeyboard):
        self.convert_to_markdown()
        self.addText(build_keyboard_md(buttons),True)
        return self
    def addButton(self,button:KBButton):
        self.convert_to_markdown()
        self.addText(convert_button_md(button),True)
        return self
    
    def supportsButton(self):
        return True
    
            
    async def send(self,matcher:type[Matcher]|Matcher,**kwargs):
        msgpart=QQMessage()
        has_image=False
        for i in self.msg:
            if has_image and not i.is_text():
                # Send part of message
                await matcher.send(msgpart,**kwargs)
                msgpart=QQMessage()
                    
            msgpart.append(i)
            if not i.is_text():
                has_image=True
        await matcher.send(msgpart,**kwargs)