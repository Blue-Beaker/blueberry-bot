import os
import sys
from pathlib import Path

# 将 blueberry-bot/blueberry-bot/（含 plugins 包）加入 sys.path
_plugins_root = Path(__file__).resolve().parent / "blueberry-bot"
if str(_plugins_root) not in sys.path:
    sys.path.insert(0, str(_plugins_root))

# 设置 NoneBot logger 的日志级别（测试中未调用 nonebot.init()，
# 需手动注入 loguru 的 nonebot_log_level extra 才能生效）
os.environ.setdefault("LOG_LEVEL", "DEBUG")

from loguru import logger as _loguru_logger  # noqa: E402

_loguru_logger.configure(extra={"nonebot_log_level": os.environ["LOG_LEVEL"]})
