from io import BytesIO
from nonebot.plugin import PluginMetadata
from nonebot.adapters.minecraft import BaseChatEvent
from nonebot.adapters.minecraft import MessageSegment as MCMessageSegment
from nonebot.adapters.minecraft.model import HoverEvent as MCHoverEvent,BaseComponent
from .import mc_images_util

__plugin_meta__ = PluginMetadata(
    name="mc_image",
    description="",
    usage=""
)

def image_to_mc_text(text: str, image: str|bytes) -> MCMessageSegment|str:
    if isinstance(image,str):
        img=image
    else:
        img=BytesIO(image)
    img_text=mc_images_util.image_to_mc_text(img)
    return img_text

    message=MCMessageSegment.text(text,hover_event=MCHoverEvent(action="show_text",text=[BaseComponent(text=mc_images_util.image_to_mc_text(img))]))
    
    # Support older versions of Minecraft that don't have the "contents" field in hover events
    # message.data["hoverEvent"]["value"]=message.data["hoverEvent"]["contents"]
    
    return message