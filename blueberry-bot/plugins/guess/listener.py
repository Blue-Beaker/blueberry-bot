# ── profile_link 事件监听器 ──────────────────────────

from nonebot import logger
from ..bbot_api.profile_link.profile_link import get_profile_link_manager
from ..bbot_api.profile_link.events import on_link, LinkUserEvent, UnlinkUserEvent


@on_link(LinkUserEvent)
def _guess_on_link(event: LinkUserEvent):
    from .handler_base import INSTANCES
    manager = get_profile_link_manager()
    if manager.migrate_dict(INSTANCES.guessManagers, event.raw_id, event.profile_id):
        logger.info(f"guess: 已迁移会话 {event.raw_id} -> {event.profile_id}")

@on_link(UnlinkUserEvent)
def _guess_on_unlink(event: UnlinkUserEvent):
    from .handler_base import INSTANCES
    manager = get_profile_link_manager()
    if manager.migrate_dict(INSTANCES.guessManagers, event.profile_id, event.raw_id):
        logger.info(f"guess: 已回迁会话 {event.profile_id} -> {event.raw_id}")
