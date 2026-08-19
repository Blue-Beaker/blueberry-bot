# ── profile_link 事件监听器 ──────────────────────────

from nonebot import logger
from ..bbot_api.profile_link.profile_link import get_profile_link_manager
from ..bbot_api.profile_link.events import on_link, LinkUserEvent, UnlinkUserEvent


@on_link(LinkUserEvent)
def _orb_on_link(event: LinkUserEvent):
    from . import ORB_STORAGE, _migrate_balance, get_balance
    if _migrate_balance(event.raw_id, event.profile_id):
        ORB_STORAGE.needs_save = True
        logger.info(f"orb: 已迁移余额 {event.raw_id} -> {event.profile_id}")
        logger.info(f"{event.profile_id}: {get_balance(event.profile_id)}")

@on_link(UnlinkUserEvent)
def _orb_on_unlink(event: UnlinkUserEvent):
    from . import ORB_STORAGE, _migrate_balance, get_balance
    manager = get_profile_link_manager()
    profile = manager.get_user_profile(event.profile_id)
    # 只有解绑后 profile 不再关联任何实际 ID 时，才把 orb 回退到 raw_id
    if profile and len(profile.linked_ids) == 0:
        if _migrate_balance(event.profile_id, event.raw_id):
            ORB_STORAGE.needs_save = True
            logger.info(f"orb: 已回迁余额 {event.profile_id} -> {event.raw_id}")
            logger.info(f"{event.profile_id}: {get_balance(event.profile_id)}")
            logger.info(f"{event.raw_id}: {get_balance(event.raw_id)}")
    else:
        logger.info(f"orb: 跳过回迁 (profile {event.profile_id} 仍有其他绑定)")
