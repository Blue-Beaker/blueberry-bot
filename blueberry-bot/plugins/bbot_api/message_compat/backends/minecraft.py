from nonebot import require

from nonebot.adapters.minecraft import Bot as MCBot, BaseChatEvent as MCBaseChatEvent, Message as MCMessage, MessageSegment as MCMessageSegment

try:
    require("bbot_mc_image")
    from ....bbot_mc_image import image_to_mc_text
except:
    image_to_mc_text=None

