import sys
from pathlib import Path

# 将 blueberry-bot/blueberry-bot/（含 plugins 包）加入 sys.path
_plugins_root = Path(__file__).resolve().parent / "blueberry-bot"
if str(_plugins_root) not in sys.path:
    sys.path.insert(0, str(_plugins_root))
