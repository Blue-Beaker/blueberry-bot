from nonebot.internal.adapter import Message
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment
from nonebot.adapters.qq.models import MessageKeyboard,InlineKeyboard,InlineKeyboardRow,Button,Action,RenderData
from urllib.parse import quote,unquote

from ..buttons import ButtonKeyboard,KBButton

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