"""group_config 插件入口 — 管理 PermGroupManager 生命周期。"""

from pathlib import Path

from nonebot import get_driver, logger
from .permgroup_manager import get_permgroup_manager

driver = get_driver()

# 已知的可能包含旧 permgroup 映射的配置文件
_KNOWN_CONFIG_PATHS = [
    "config/bbot_perms.json",
    "config/orb_data.json",
    "config/say_config.json",
    "config/ob_interaction.json",
]


@driver.on_startup
async def _load_permgroup_map():
    mgr = get_permgroup_manager()
    mgr.load()
    
    # 从旧配置文件迁移（取并集）
    migrated = mgr.migrate_from_configs(_KNOWN_CONFIG_PATHS)
    if migrated:
        mgr.save()
        logger.info("已从旧配置文件迁移 permgroup 映射并保存")
    
    logger.info(f"已加载 permgroup 映射: {len(mgr.permgroup_groups_map)} 个权限组, "
                f"{sum(len(v) for v in mgr.permgroup_groups_map.values())} 条绑定")


@driver.on_shutdown
async def _save_permgroup_map():
    mgr = get_permgroup_manager()
    mgr.save()
    logger.info(f"已保存 permgroup 映射")
