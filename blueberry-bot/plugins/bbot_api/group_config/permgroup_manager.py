"""PermGroupManager — 全局权限组映射管理器。

独立于 GroupConfig，所有 GroupConfig 实例共用同一套 permgroup 映射。
映射关系存储在单独的配置文件中。
"""

import json
import os
from pathlib import Path
from typing import Any

from nonebot import logger

# 默认配置文件路径
PERMGROUP_MAP_PATH = Path("config/permgroup_map.json")


class PermGroupManager:
    """权限组映射管理器。
    
    管理 permgroup_name → [group_id, ...] 的映射，
    并维护 group → [permgroup_name, ...] 的反向缓存。
    所有 GroupConfig 实例共享此管理器。
    """
    
    permgroup_groups_map: dict[str, list[str]]  # permgroup_name → [group_id, ...]
    _group_permgroup_cache: dict[str, list[str]] | None  # group → [permgroup_name, ...], 懒构建
    config_path: str
    
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.permgroup_groups_map = {}
        self._group_permgroup_cache = None
        self.config_path = str(config_path or PERMGROUP_MAP_PATH)
    
    # ── 缓存 ─────────────────────────────────────────────
    
    def _build_cache(self) -> dict[str, list[str]]:
        """从 permgroup_groups_map 反转构建 group→[permgroup_name] 缓存。"""
        cache: dict[str, list[str]] = {}
        for pg_name, groups in self.permgroup_groups_map.items():
            for g in groups:
                if g not in cache:
                    cache[g] = []
                if pg_name not in cache[g]:
                    cache[g].append(pg_name)
        return cache
    
    def get_group_permgroups(self, group: str) -> list[str]:
        """获取群组附加的所有权限组名称。"""
        if self._group_permgroup_cache is None:
            self._group_permgroup_cache = self._build_cache()
        return list(self._group_permgroup_cache.get(group, []))
    
    def _invalidate_cache(self) -> None:
        self._group_permgroup_cache = None
    
    # ── 映射操作 ─────────────────────────────────────────
    
    def bind(self, group: str, permgroup_name: str) -> None:
        """将权限组附加到群组。"""
        if permgroup_name not in self.permgroup_groups_map:
            self.permgroup_groups_map[permgroup_name] = []
        if group not in self.permgroup_groups_map[permgroup_name]:
            self.permgroup_groups_map[permgroup_name].append(group)
        self._invalidate_cache()
    
    def unbind(self, group: str, permgroup_name: str | None = None) -> list[str]:
        """解除群组的权限组附加。
        
        permgroup_name=None 时解除该群组所有绑定。
        返回实际解除了的权限组名称列表。
        """
        removed: list[str] = []
        if permgroup_name is None:
            for pg_name in list(self.permgroup_groups_map):
                gs = self.permgroup_groups_map[pg_name]
                if group in gs:
                    gs.remove(group)
                    removed.append(pg_name)
                    if not gs:
                        del self.permgroup_groups_map[pg_name]
        else:
            gs = self.permgroup_groups_map.get(permgroup_name)
            if gs and group in gs:
                gs.remove(group)
                removed.append(permgroup_name)
                if not gs:
                    del self.permgroup_groups_map[permgroup_name]
        if removed:
            self._invalidate_cache()
        return removed
    
    def list_group_binds(self) -> dict[str, list[str]]:
        """返回所有 group→permgroup 映射（由 cache 构建）。"""
        return dict(sorted(self._build_cache().items()))
    
    def list_permgroup_binds(self, permgroup_name: str) -> list[str]:
        """获取权限组绑定到的所有群组 ID。"""
        return list(self.permgroup_groups_map.get(permgroup_name, []))
    
    def clear_permgroup_binds(self, permgroup_name: str) -> None:
        """清除权限组的所有绑定。"""
        if permgroup_name in self.permgroup_groups_map:
            del self.permgroup_groups_map[permgroup_name]
            self._invalidate_cache()
    
    # ── 持久化 ───────────────────────────────────────────
    
    def save(self) -> None:
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        data = {
            "permgroup_groups_map": {
                pg: list(gs) for pg, gs in self.permgroup_groups_map.items()
            },
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> None:
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"加载 permgroup_map 失败: {e}")
            return
        if not isinstance(data, dict):
            return
        
        map_data = data.get("permgroup_groups_map")
        if isinstance(map_data, dict):
            self.permgroup_groups_map = {}
            for k, v in map_data.items():
                if isinstance(v, list):
                    self.permgroup_groups_map[str(k)] = [str(x) for x in v]
                elif isinstance(v, str):
                    self.permgroup_groups_map[str(k)] = [v]
        self._invalidate_cache()
    
    # ── 旧配置迁移 ───────────────────────────────────────
    
    def migrate_from_configs(self, config_paths: list[str]) -> bool:
        """从旧 GroupConfig JSON 文件中迁移 permgroup 映射。
        
        扫描所有给定路径的 JSON 文件，提取其中可能存在的
        permgroup_groups_map 或 group_permgroup_map 字段，
        合并到当前管理器（取并集）。
        
        返回是否发生了迁移。
        """
        migrated = False
        
        for path in config_paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(data, dict):
                continue
            
            # 尝试新格式 permgroup_groups_map
            map_data = data.get("permgroup_groups_map")
            if isinstance(map_data, dict) and map_data:
                for pg_name, groups in map_data.items():
                    pg_name = str(pg_name)
                    if isinstance(groups, list):
                        for g in groups:
                            self.bind(str(g), pg_name)
                    elif isinstance(groups, str):
                        self.bind(str(groups), pg_name)
                migrated = True
                logger.info(f"从 {path} 迁移了 permgroup_groups_map")
            
            # 尝试旧格式 group_permgroup_map（需要反转）
            old_data = data.get("group_permgroup_map")
            if isinstance(old_data, dict) and old_data:
                for g, pgns in old_data.items():
                    if isinstance(pgns, str):
                        pgns = [pgns]
                    if isinstance(pgns, list):
                        for pg_name in pgns:
                            self.bind(str(g), str(pg_name))
                migrated = True
                logger.info(f"从 {path} 迁移了 group_permgroup_map（旧格式）")
        
        return migrated


# 全局单例
_permgroup_manager: PermGroupManager | None = None


def get_permgroup_manager() -> PermGroupManager:
    """获取全局 PermGroupManager 单例。"""
    global _permgroup_manager
    if _permgroup_manager is None:
        _permgroup_manager = PermGroupManager()
    return _permgroup_manager


def set_permgroup_manager(manager: PermGroupManager) -> None:
    """设置全局 PermGroupManager 单例（用于测试）。"""
    global _permgroup_manager
    _permgroup_manager = manager
