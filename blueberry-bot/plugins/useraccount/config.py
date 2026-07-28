"""useraccount 插件配置与数据管理。"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from nonebot import logger

# 数据文件路径
DATA_PATH = Path("config/useraccount")
DATA_PATH.mkdir(parents=True, exist_ok=True)
PENDING_LINKS_PATH = DATA_PATH / "pending_links.json"


@dataclass
class PendingLink:
    """待确认的 link 请求。"""
    token: str
    profile_id: str
    raw_id: str
    created_at: int
    expires_at: int


def load_pending_links() -> dict[str, PendingLink]:
    """加载待确认的 link 请求。"""
    if not PENDING_LINKS_PATH.exists():
        return {}
    try:
        with open(PENDING_LINKS_PATH) as f:
            data = json.load(f)
        pending = {}
        for token, d in data.items():
            if isinstance(d, dict):
                pending[token] = PendingLink(**d)
        return pending
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"加载 pending_links 失败: {e}")
        return {}


def save_pending_links(pending: dict[str, PendingLink]) -> None:
    """保存待确认的 link 请求。"""
    data = {token: asdict(pl) for token, pl in pending.items()}
    with open(PENDING_LINKS_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
