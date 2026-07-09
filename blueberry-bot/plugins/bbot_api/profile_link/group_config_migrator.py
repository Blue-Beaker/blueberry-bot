"""GroupConfig 配置迁移器。
    
当 link 事件发生时，将 raw_id 的 GroupConfig 配置合并/拆分到 profile_id。
"""
import re
from nonebot import logger


def _migrate_group_key(key: str) -> str:
    """将旧格式 group key 迁移为带前缀的新格式。
    
    根据 ID 形式推断平台前缀（与 get_raw_id 格式一致）:
      - 不超过 10 位纯数字 → group_ (OneBot 群号)
      - 超过 10 位纯数字 → dc_ (Discord 频道 ID)
      - 32 位大写十六进制 → qqgroup_ (QQ 群 openid)
      - 其他格式保持不变（如 "global", "private", profile 名称等）
    """
    if re.fullmatch(r"\d{1,10}", key):
        return f"group_{key}"
    if re.fullmatch(r"\d+", key):
        return f"dc_{key}"
    if re.fullmatch(r"[0-9A-F]{32}", key):
        return f"qqgroup_{key}"
    return key


def _find_raw_overrides(config, raw_id: str):
    """在 config.group_overrides 中查找 raw_id 对应的 override。
    
    同时尝试带前缀和不带前缀两种格式。
    返回 (matched_key, overrides) 或 (None, None)。
    """
    # 直接查找
    if raw_id in config.group_overrides:
        return raw_id, config.group_overrides[raw_id]
    
    # 尝试旧格式（去掉前缀后的纯数字/ID）
    for prefix in ("group_", "dc_", "qqgroup_", "mc_", "u_", "qquser_"):
        if raw_id.startswith(prefix):
            stripped = raw_id[len(prefix):]
            if stripped in config.group_overrides:
                return stripped, config.group_overrides[stripped]
            break
    
    # 尝试旧格式（纯数字 → 带前缀）
    migrated = _migrate_group_key(raw_id)
    if migrated != raw_id and migrated in config.group_overrides:
        return migrated, config.group_overrides[migrated]
    
    return None, None


def migrate_group_config(config, profile_id: str, raw_id: str) -> bool:
    """将 raw_id 的 GroupConfig 配置合并到 profile_id 下。
    
    合并规则：
    - profile_id 作为下层，raw_id 作为上层
    - raw_id 有值的字段覆盖到 profile_id
    - 两层都未覆写的字段保持空白
    - 合并后删除 raw_id 的 override 条目
    
    返回是否发生了变更。
    """
    if profile_id == raw_id:
        return False
    
    matched_key, raw_overrides = _find_raw_overrides(config, raw_id)
    if raw_overrides is None:
        return False
    
    profile_overrides = config.group_overrides.get(profile_id)
    
    raw_fields = {k: v for k, v in raw_overrides.to_dict().items() if v is not None}
    if not raw_fields:
        del config.group_overrides[matched_key]
        return True
    
    if profile_overrides is None:
        config.group_overrides[profile_id] = raw_overrides
    else:
        for key, value in raw_fields.items():
            setattr(profile_overrides, key, value)
    
    del config.group_overrides[matched_key]
    return True


def unmigrate_group_config(config, profile_id: str, raw_id: str) -> bool:
    """将 profile_id 的配置拆分回 raw_id（用于解绑）。
    
    返回是否发生了变更。
    """
    if profile_id == raw_id:
        return False
    
    profile_overrides = config.group_overrides.get(profile_id)
    if profile_overrides is None:
        return False
    
    raw_config = config.config_class()
    raw_config.load_dict(profile_overrides.to_dict())
    config.group_overrides[raw_id] = raw_config
    return True
