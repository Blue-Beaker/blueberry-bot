import json
import os
import re
from typing import Any


def infer_platform(raw_id: str) -> str:
    """根据原始用户 ID 推断平台前缀（与 get_raw_id 格式一致）。
    
    规则:
      - 10 位以内纯数字 → u_ (OneBot QQ号)
      - 10位以上纯数字 → dc_ (Discord ID)
      - 32位大写十六进制 → qquser_ (QQ openid)
      - 其他 → mc_ (Minecraft)
    """
    if re.fullmatch(r"\d{1,10}", raw_id):
        return "u"
    if re.fullmatch(r"\d+", raw_id):
        return "dc"
    if re.fullmatch(r"[0-9A-F]{32}", raw_id):
        return "qquser"
    return "mc"


def migrate_key(old_key: str) -> str:
    """将旧版 raw key 迁移为带平台前缀的新格式（与 get_raw_id 一致）。"""
    return f"{infer_platform(old_key)}_{old_key}"


class OrbStorage:
    balances: dict[str, int]
    config_path: str | None
    
    def __init__(self, config_path: str | None = None) -> None:
        self.balances = {}
        self.config_path = config_path
    
    def to_dict(self):
        return {"balances": self.balances, "version": 2}
    
    def load_dict(self, data: dict[str, Any]):
        version = data.get("version", 1)
        balances = data.get("balances", {})
        
        if version < 2:
            # v1 → v2: 自动迁移 key 格式
            migrated = {}
            for old_key, value in balances.items():
                new_key = migrate_key(old_key)
                migrated[new_key] = value
            self.balances = migrated
        else:
            self.balances = balances
    
    def save(self) -> None:
        if not self.config_path:
            return
        
        # 保存前备份原文件（仅 v1 格式需要备份）
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    old_data = json.load(f)
                if isinstance(old_data, dict) and old_data.get("version", 1) < 2:
                    bak_path = self.config_path + ".bak_v1"
                    if not os.path.exists(bak_path):
                        with open(bak_path, "w") as f:
                            json.dump(old_data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
        
        data = self.to_dict()
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> None:
        if not self.config_path or not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(data, dict):
            return
        self.load_dict(data)
    
    def get_balance(self, user: str) -> int:
        if user not in self.balances:
            self.balances[user] = 0
        return self.balances.get(user, 0)
    
    def add_balance(self, user: str, count: int, allow_negative: bool = False) -> bool:
        changed = self.get_balance(user) + count
        if not allow_negative and count < 0 and changed < 0:
            return False
        self.balances[user] = changed
        return True