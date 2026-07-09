import json
import os
from typing import Any


class UserProfile:
    """用户绑定条目。
    
    将多个平台的实际用户 ID 绑定到一个通用 ID 下。
    """
    name: str
    linked_ids: list[str]
    
    def __init__(self, name: str, linked_ids: list[str] | None = None):
        self.name = name
        self.linked_ids = linked_ids or []
    
    def to_dict(self) -> dict[str, Any]:
        return {"linked_ids": self.linked_ids}
    
    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "UserProfile":
        return cls(name=name, linked_ids=data.get("linked_ids", []))


class GroupProfile:
    """群组绑定条目。
    
    将多个平台的实际群 ID 绑定到一个通用 ID 下。
    """
    name: str
    linked_ids: list[str]
    
    def __init__(self, name: str, linked_ids: list[str] | None = None):
        self.name = name
        self.linked_ids = linked_ids or []
    
    def to_dict(self) -> dict[str, Any]:
        return {"linked_ids": self.linked_ids}
    
    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "GroupProfile":
        return cls(name=name, linked_ids=data.get("linked_ids", []))


class ProfileLinkManager:
    """profile link 管理器。
    
    用户绑定和群组绑定分离存储，各自独立管理。
    数据文件: config/profile_links.json
    """
    
    user_links: dict[str, UserProfile]    # key = 通用用户 ID
    group_links: dict[str, GroupProfile]  # key = 通用群 ID
    config_path: str
    
    def __init__(self, config_path: str = "config/profile_links.json"):
        self.user_links = {}
        self.group_links = {}
        self.config_path = config_path
    
    # ═══════════════════════════════════════════════════
    #  用户绑定
    # ═══════════════════════════════════════════════════
    
    def get_user_profile(self, profile_id: str) -> UserProfile | None:
        return self.user_links.get(profile_id)
    
    def find_user_by_linked_id(self, raw_id: str) -> UserProfile | None:
        for profile in self.user_links.values():
            if raw_id in profile.linked_ids:
                return profile
        return None
    
    def resolve_user_id(self, raw_id: str) -> str:
        profile = self.find_user_by_linked_id(raw_id)
        return profile.name if profile else raw_id
    
    def get_all_user_linked_ids(self, profile_id: str) -> list[str]:
        profile = self.user_links.get(profile_id)
        if not profile:
            return [profile_id]
        return [profile_id] + [id for id in profile.linked_ids if id != profile_id]
    
    def create_user_profile(self, name: str) -> UserProfile:
        if name in self.user_links:
            raise ValueError(f"通用用户 ID '{name}' 已存在")
        profile = UserProfile(name=name)
        self.user_links[name] = profile
        return profile
    
    def delete_user_profile(self, profile_id: str) -> bool:
        if profile_id in self.user_links:
            del self.user_links[profile_id]
            self._emit_event("ProfileDeleteEvent", profile_id=profile_id)
            return True
        return False
    
    def link_user_id(self, profile_id: str, raw_id: str) -> None:
        if profile_id not in self.user_links:
            raise ValueError(f"通用用户 ID '{profile_id}' 不存在")
        existing = self.find_user_by_linked_id(raw_id)
        if existing and existing.name != profile_id:
            raise ValueError(f"'{raw_id}' 已被 '{existing.name}' 绑定")
        if raw_id not in self.user_links[profile_id].linked_ids:
            self.user_links[profile_id].linked_ids.append(raw_id)
            self._emit_event("LinkUserEvent", profile_id=profile_id, raw_id=raw_id)
    
    def unlink_user_id(self, profile_id: str, raw_id: str) -> None:
        if profile_id not in self.user_links:
            raise ValueError(f"通用用户 ID '{profile_id}' 不存在")
        if raw_id in self.user_links[profile_id].linked_ids:
            self.user_links[profile_id].linked_ids.remove(raw_id)
            self._emit_event("UnlinkUserEvent", profile_id=profile_id, raw_id=raw_id)
    
    # ═══════════════════════════════════════════════════
    #  群组绑定
    # ═══════════════════════════════════════════════════
    
    def get_group_profile(self, profile_id: str) -> GroupProfile | None:
        return self.group_links.get(profile_id)
    
    def find_group_by_linked_id(self, raw_group_id: str) -> GroupProfile | None:
        for profile in self.group_links.values():
            if raw_group_id in profile.linked_ids:
                return profile
        return None
    
    def resolve_group_id(self, raw_group_id: str) -> str | None:
        profile = self.find_group_by_linked_id(raw_group_id)
        return profile.name if profile else None
    
    def get_all_group_linked_ids(self, profile_id: str) -> list[str]:
        profile = self.group_links.get(profile_id)
        if not profile:
            return [profile_id]
        return [profile_id] + [id for id in profile.linked_ids if id != profile_id]
    
    def create_group_profile(self, name: str) -> GroupProfile:
        if name in self.group_links:
            raise ValueError(f"通用群 ID '{name}' 已存在")
        profile = GroupProfile(name=name)
        self.group_links[name] = profile
        return profile
    
    def delete_group_profile(self, profile_id: str) -> bool:
        if profile_id in self.group_links:
            del self.group_links[profile_id]
            self._emit_event("ProfileDeleteEvent", profile_id=profile_id)
            return True
        return False
    
    def link_group_id(self, profile_id: str, raw_group_id: str) -> None:
        if profile_id not in self.group_links:
            raise ValueError(f"通用群 ID '{profile_id}' 不存在")
        existing = self.find_group_by_linked_id(raw_group_id)
        if existing and existing.name != profile_id:
            raise ValueError(f"群 '{raw_group_id}' 已被 '{existing.name}' 绑定")
        if raw_group_id not in self.group_links[profile_id].linked_ids:
            self.group_links[profile_id].linked_ids.append(raw_group_id)
            self._emit_event("LinkGroupEvent", profile_id=profile_id, raw_group_id=raw_group_id)
    
    def unlink_group_id(self, profile_id: str, raw_group_id: str) -> None:
        if profile_id not in self.group_links:
            raise ValueError(f"通用群 ID '{profile_id}' 不存在")
        if raw_group_id in self.group_links[profile_id].linked_ids:
            self.group_links[profile_id].linked_ids.remove(raw_group_id)
            self._emit_event("UnlinkGroupEvent", profile_id=profile_id, raw_group_id=raw_group_id)
    
    # ═══════════════════════════════════════════════════
    #  事件
    # ═══════════════════════════════════════════════════
    
    def _emit_event(self, event_name: str, **kwargs: Any) -> None:
        try:
            from . import events as _events
            bus = _events.get_event_bus()
            event_class = getattr(_events, event_name)
            event = event_class(**kwargs)
            bus.emit(event)
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════
    #  持久化
    # ═══════════════════════════════════════════════════
    
    def save(self) -> None:
        data = {
            "version": 2,
            "user_links": {
                name: p.to_dict() for name, p in self.user_links.items()
            },
            "group_links": {
                name: p.to_dict() for name, p in self.group_links.items()
            },
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> None:
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(data, dict):
            return
        
        # v1 → v2 迁移：旧格式拆分为 user_links + group_links
        version = data.get("version", 1)
        if version < 2:
            # v1 格式: {"links": {"name": {"linked_ids": [...], "group_ids": [...]}}}
            # 更老格式: {"name": {"linked_ids": [...], "group_ids": [...]}}
            old_links = data.get("links") if "links" in data else data
            if not isinstance(old_links, dict):
                return
            for name, entry in old_links.items():
                if not isinstance(entry, dict) or name == "version":
                    continue
                linked = entry.get("linked_ids", [])
                groups = entry.get("group_ids", [])
                if isinstance(linked, list) and linked:
                    self.user_links[name] = UserProfile(name=name, linked_ids=linked)
                if isinstance(groups, list) and groups:
                    self.group_links[name] = GroupProfile(name=name, linked_ids=groups)
            return
        
        user_data = data.get("user_links", {})
        self.user_links = {
            name: UserProfile.from_dict(name, d)
            for name, d in user_data.items() if isinstance(d, dict)
        }
        group_data = data.get("group_links", {})
        self.group_links = {
            name: GroupProfile.from_dict(name, d)
            for name, d in group_data.items() if isinstance(d, dict)
        }

    # ── 数据迁移工具 ─────────────────────────────────────
    
    def migrate_dict(self, d: dict[str, Any], raw_id: str, profile_id: str) -> bool:
        changed = False
        if raw_id in d:
            if profile_id not in d:
                d[profile_id] = d[raw_id]
            del d[raw_id]
            changed = True
        return changed

    # ── 数据合并工具 ─────────────────────────────────────
    
    def sum_values(self, profile_id: str, getter) -> int:
        total = 0
        for linked_id in self.get_all_user_linked_ids(profile_id):
            total += getter(linked_id)
        return total
    
    def merge_override(self, profile_id: str, getter):
        for linked_id in self.get_all_user_linked_ids(profile_id):
            value = getter(linked_id)
            if value is not None:
                return value
        return None


# 全局单例
_PROFILE_LINK_MANAGER: ProfileLinkManager | None = None


def get_profile_link_manager() -> ProfileLinkManager:
    global _PROFILE_LINK_MANAGER
    if _PROFILE_LINK_MANAGER is None:
        _PROFILE_LINK_MANAGER = ProfileLinkManager()
    return _PROFILE_LINK_MANAGER


def set_profile_link_manager(manager: ProfileLinkManager) -> None:
    global _PROFILE_LINK_MANAGER
    _PROFILE_LINK_MANAGER = manager
