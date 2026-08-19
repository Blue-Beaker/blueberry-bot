
# ── profile_link 事件监听器 ──────────────────────────

from ..bbot_api.profile_link.group_config_migrator import migrate_group_config, unmigrate_group_config
from ..bbot_api.profile_link.events import on_link, LinkUserEvent, LinkGroupEvent, UnlinkUserEvent, UnlinkGroupEvent

@on_link(LinkUserEvent)
def _say_on_link(event: LinkUserEvent):
    if migrate_group_config(say_config, event.profile_id, event.raw_id):
        logger.info(f"say: 已合并配置 {event.raw_id} → {event.profile_id}")

@on_link(UnlinkUserEvent)
def _say_on_unlink(event: UnlinkUserEvent):
    if unmigrate_group_config(say_config, event.profile_id, event.raw_id):
        logger.info(f"say: 已拆分配置 {event.profile_id} → {event.raw_id}")

@on_link(LinkGroupEvent)
def _say_on_link_group(event: LinkGroupEvent):
    if migrate_group_config(say_config, event.profile_id, event.raw_group_id):
        logger.info(f"say: 已合并群配置 {event.raw_group_id} → {event.profile_id}")

@on_link(UnlinkGroupEvent)
def _say_on_unlink_group(event: UnlinkGroupEvent):
    if unmigrate_group_config(say_config, event.profile_id, event.raw_group_id):
        logger.info(f"say: 已拆分群配置 {event.profile_id} → {event.raw_group_id}")