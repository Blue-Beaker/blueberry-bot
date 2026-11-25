from enum import Enum
from typing import Any, get_type_hints


class Platform(Enum):
    """mod 支持的平台，对应 API 的 platform 参数。"""

    WIN = "win"
    ANDROID32 = "android32"
    ANDROID64 = "android64"
    MAC_INTEL = "mac-intel"
    MAC_ARM = "mac-arm"
    IOS = "ios"


class ModSearchArgs:
    """mod 搜索参数。

    直接对应 Geode Index /v1/mods 的查询参数，通过 getData() 转成请求参数。
    未设置的字段不会出现在请求中。
    """

    # 分页
    page: int = 1
    per_page: int = 10

    # 搜索
    query: str | None = None
    developer: str | None = None

    # 过滤
    tags: str | list[str] | None = None
    gd: str | None = None
    geode: str | None = None
    platform: Platform | str | None = None

    def getData(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for k in get_type_hints(type(self)):
            v = getattr(self, k, None)
            if v is None:
                continue
            if isinstance(v, Enum):
                v = v.value
            elif isinstance(v, list):
                v = ",".join(str(i) for i in v)
            data[k] = v
        return data
