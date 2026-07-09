"""profile_link 事件监听器。
"""
from nonebot import logger

from .events import on_link, LinkUserEvent, LinkGroupEvent, UnlinkUserEvent, UnlinkGroupEvent
from .profile_link import get_profile_link_manager


# ── guess 插件 ────────────────────────────────────────

def register_guess_listeners():
    try:
        from ...guess.handler_base import INSTANCES
        
        @on_link(LinkUserEvent)
        def _guess_on_link(event: LinkUserEvent):
            manager = get_profile_link_manager()
            if manager.migrate_dict(INSTANCES.guessManagers, event.raw_id, event.profile_id):
                logger.info(f"guess: 已迁移会话 {event.raw_id} → {event.profile_id}")
        
        @on_link(UnlinkUserEvent)
        def _guess_on_unlink(event: UnlinkUserEvent):
            manager = get_profile_link_manager()
            if manager.migrate_dict(INSTANCES.guessManagers, event.profile_id, event.raw_id):
                logger.info(f"guess: 已回迁会话 {event.profile_id} → {event.raw_id}")
        
        logger.debug("profile_link: guess 监听器已注册")
    except Exception as e:
        logger.warning(f"profile_link: 注册 guess 监听器失败: {e}")


# ── gdguess 插件 ──────────────────────────────────────

def register_gdguess_listeners():
    try:
        from ... import gdguess as gdguess_module
        
        session_manager = gdguess_module.session_manager
        config_manager = gdguess_module.config_manager
        
        @on_link(LinkUserEvent)
        def _gdguess_on_link(event: LinkUserEvent):
            manager = get_profile_link_manager()
            if manager.migrate_dict(session_manager.entries, event.raw_id, event.profile_id):
                logger.info(f"gdguess: 已迁移会话 {event.raw_id} → {event.profile_id}")
            if config_manager.merge_profile(event.profile_id, event.raw_id):
                logger.info(f"gdguess: 已合并配置 {event.raw_id} → {event.profile_id}")
        
        @on_link(UnlinkUserEvent)
        def _gdguess_on_unlink(event: UnlinkUserEvent):
            manager = get_profile_link_manager()
            if manager.migrate_dict(session_manager.entries, event.profile_id, event.raw_id):
                logger.info(f"gdguess: 已回迁会话 {event.profile_id} → {event.raw_id}")
            if config_manager.unmerge_profile(event.profile_id, event.raw_id):
                logger.info(f"gdguess: 已拆分配置 {event.profile_id} → {event.raw_id}")
        
        logger.debug("profile_link: gdguess 监听器已注册")
    except Exception as e:
        logger.warning(f"profile_link: 注册 gdguess 监听器失败: {e}")


# ── orb_api 插件 ──────────────────────────────────────

def register_orb_listeners():
    try:
        from ... import orb_api as orb_module
        
        orb_storage = orb_module.ORB_STORAGE
        
        @on_link(LinkUserEvent)
        def _orb_on_link(event: LinkUserEvent):
            manager = get_profile_link_manager()
            if manager.migrate_dict(orb_storage.balances, event.raw_id, event.profile_id):
                logger.info(f"orb: 已迁移余额 {event.raw_id} → {event.profile_id}")
        
        @on_link(UnlinkUserEvent)
        def _orb_on_unlink(event: UnlinkUserEvent):
            manager = get_profile_link_manager()
            if manager.migrate_dict(orb_storage.balances, event.profile_id, event.raw_id):
                logger.info(f"orb: 已回迁余额 {event.profile_id} → {event.raw_id}")
        
        logger.debug("profile_link: orb 监听器已注册")
    except Exception as e:
        logger.warning(f"profile_link: 注册 orb 监听器失败: {e}")


# ── GroupConfig 通用迁移 ─────────────────────────────

def register_group_config_listener(group_config, name: str):
    @on_link(LinkUserEvent)
    def _gc_on_link(event: LinkUserEvent):
        if group_config.merge_profile(event.profile_id, event.raw_id):
            logger.info(f"{name}: 已合并配置 {event.raw_id} → {event.profile_id}")
    
    @on_link(UnlinkUserEvent)
    def _gc_on_unlink(event: UnlinkUserEvent):
        if group_config.unmerge_profile(event.profile_id, event.raw_id):
            logger.info(f"{name}: 已拆分配置 {event.profile_id} → {event.raw_id}")
    
    @on_link(LinkGroupEvent)
    def _gc_on_link_group(event: LinkGroupEvent):
        if group_config.merge_profile(event.profile_id, event.raw_group_id):
            logger.info(f"{name}: 已合并群配置 {event.raw_group_id} → {event.profile_id}")
    
    @on_link(UnlinkGroupEvent)
    def _gc_on_unlink_group(event: UnlinkGroupEvent):
        if group_config.unmerge_profile(event.profile_id, event.raw_group_id):
            logger.info(f"{name}: 已拆分群配置 {event.profile_id} → {event.raw_group_id}")


def register_say_listeners():
    try:
        from ... import say as say_module
        register_group_config_listener(say_module.say_config, "say")
        logger.debug("profile_link: say 监听器已注册")
    except Exception as e:
        logger.warning(f"profile_link: 注册 say 监听器失败: {e}")


def register_gus_listeners():
    try:
        from ... import gus as gus_module
        register_group_config_listener(gus_module.group_config, "gus")
        logger.debug("profile_link: gus 监听器已注册")
    except Exception as e:
        logger.warning(f"profile_link: 注册 gus 监听器失败: {e}")


def register_ob_interaction_listeners():
    try:
        from ... import ob_interaction as ob_interaction_module
        register_group_config_listener(ob_interaction_module.group_config, "ob_interaction")
        logger.debug("profile_link: ob_interaction 监听器已注册")
    except Exception as e:
        logger.warning(f"profile_link: 注册 ob_interaction 监听器失败: {e}")


# ── 全部注册 ──────────────────────────────────────────

_registered = False

def register_all():
    global _registered
    if _registered:
        return
    _registered = True
    
    register_guess_listeners()
    register_gdguess_listeners()
    register_orb_listeners()
    register_say_listeners()
    register_gus_listeners()
    register_ob_interaction_listeners()
    logger.info("profile_link: 监听器注册完成")
