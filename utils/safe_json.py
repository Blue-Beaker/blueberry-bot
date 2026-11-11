"""JSON 缓存文件的安全读取工具。

缓存文件可能因为写入中断、磁盘满、进程被杀等原因损坏（空文件/半截内容），
直接 json.load 会抛 JSONDecodeError 并中断启动流程。这里统一兜底。
"""
import json
from typing import Any

from nonebot import logger


def safe_load_json(path: str, default: Any = None, name: str = "") -> Any:
    """读取 JSON 文件，任何解析/IO 错误都返回 default 并记录日志。"""
    label = name or path
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"缓存文件 [{label}] 内容损坏，已忽略: {e}")
        return default
    except OSError as e:
        logger.error(f"读取缓存文件 [{label}] 失败，已忽略: {e}")
        return default
