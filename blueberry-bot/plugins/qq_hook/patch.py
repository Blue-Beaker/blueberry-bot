from typing import Any, Type, Union
from nonebot.adapters import Bot
from nonebot.adapters.discord import Message as DCMessage,MessageSegment as DCMessageSegment,Bot as DCBot
from nonebot.adapters.onebot.v11 import Bot as OBBot,Message as OBMessage,MessageSegment as OBMessageSegment
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage, MessageSegment as QQMessageSegment
from nonebot.adapters.minecraft import Bot as MCBot, Message as MCMessage

def _patch_qq_adapter():
    """
    TODO: 当适配器修复时移除本补丁.
    
    修复 nonebot QQ 适配器本地文件发送时不带文件名的问题.

    适配器 ``Bot._extract_qq_media`` 仅在文件大于 10MB 时才会填充
    ``file_name``, 而 ``send_to_c2c`` / ``send_to_group`` 正是依据
    ``media_kwargs`` 中是否存在 ``file_name`` 来决定走分片上传接口
    (``post_c2c_upload`` / ``post_group_upload``, 支持自定义文件名) 还是
    普通文件接口 (``post_c2c_files`` / ``post_group_files``, 不支持文件名).

    这里改为: 只要 segment 显式提供了 ``file_name``, 就始终填充该字段,
    从而强制走支持文件名的分片上传接口.
    """
    try:
        from nonebot.adapters.qq import Bot as _QQBot
        from nonebot.adapters.qq.bot import DEFAULT_FILENAME
    except Exception:
        return

    original = _QQBot.__dict__.get("_extract_qq_media")
    if original is None:
        return
    original_func = original.__func__ if isinstance(original, staticmethod) else original
    if getattr(original_func, "_bbot_patched", False):
        return

    def _extract_qq_media(message: QQMessage) -> dict[str, Any]:
        kwargs = original_func(message)
        file_segment = (
            (message["file_image"] or None)
            or (message["file_video"] or None)
            or (message["file_audio"] or None)
            or (message["file_file"] or None)
        )
        if file_segment is not None:
            file_name = file_segment[-1].data.get("file_name")
            # 显式提供了文件名时始终走分片上传; 否则沿用适配器默认行为
            if file_name:
                kwargs["file_name"] = file_name
            elif "file_name" not in kwargs:
                kwargs["file_name"] = DEFAULT_FILENAME
        return kwargs

    _extract_qq_media._bbot_patched = True  # type: ignore[attr-defined]
    _QQBot._extract_qq_media = staticmethod(_extract_qq_media)

_patch_qq_adapter()
