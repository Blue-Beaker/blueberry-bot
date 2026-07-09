from typing import Any, Callable, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])


class LinkEvent:
    """link 事件基类。"""
    pass


class LinkUserEvent(LinkEvent):
    """用户 ID 绑定/解绑事件。"""
    def __init__(self, profile_id: str, raw_id: str):
        self.profile_id = profile_id
        self.raw_id = raw_id


class LinkGroupEvent(LinkEvent):
    """群 ID 绑定/解绑事件。"""
    def __init__(self, profile_id: str, raw_group_id: str):
        self.profile_id = profile_id
        self.raw_group_id = raw_group_id


class UnlinkUserEvent(LinkEvent):
    """用户 ID 解绑事件。"""
    def __init__(self, profile_id: str, raw_id: str):
        self.profile_id = profile_id
        self.raw_id = raw_id


class UnlinkGroupEvent(LinkEvent):
    """群 ID 解绑事件。"""
    def __init__(self, profile_id: str, raw_group_id: str):
        self.profile_id = profile_id
        self.raw_group_id = raw_group_id


class ProfileDeleteEvent(LinkEvent):
    """通用 ID 删除事件。"""
    def __init__(self, profile_id: str):
        self.profile_id = profile_id


class LinkEventBus:
    """link 事件总线。
    
    管理监听器的注册和事件分发。
    其他模块通过 ``on_link()`` 装饰器注册监听器。
    """
    
    def __init__(self):
        self._listeners: list[tuple[type[LinkEvent], Callable[..., Any]]] = []
    
    def on(self, event_type: type[LinkEvent]) -> Callable[[_F], _F]:
        """装饰器：注册指定类型事件的监听器。"""
        def decorator(listener: _F) -> _F:
            self._listeners.append((event_type, listener))
            return listener
        return decorator
    
    def emit(self, event: LinkEvent) -> None:
        """触发事件，通知所有对应类型的监听器。"""
        for event_type, listener in self._listeners:
            if isinstance(event, event_type):
                listener(event)
    
    def clear(self) -> None:
        """清除所有监听器。"""
        self._listeners.clear()


# 全局单例
_event_bus: LinkEventBus | None = None


def get_event_bus() -> LinkEventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = LinkEventBus()
    return _event_bus


def on_link(event_type: type[LinkEvent]) -> Callable[[_F], _F]:
    """快捷方式：获取全局事件总线并注册监听器。"""
    return get_event_bus().on(event_type)


def migrate_on_link(
    event_type: type[LinkEvent],
    storages: list[dict],
    get_raw_key,
    get_profile_key,
) -> None:
    """快捷方式：为 link 事件注册一个通用的 dict key 迁移监听器。
    
    参数:
        event_type: 监听的事件类型 (LinkUserEvent / LinkGroupEvent)
        storages: 需要迁移的 dict 列表
        get_raw_key: 从事件中提取旧 key 的函数
        get_profile_key: 从事件中提取新 key (通用 ID) 的函数
    """
    from .profile_link import get_profile_link_manager
    
    @on_link(event_type)
    def _migrate_listener(event: Any) -> None:
        manager = get_profile_link_manager()
        raw_key = get_raw_key(event)
        profile_key = get_profile_key(event)
        for d in storages:
            manager.migrate_dict(d, raw_key, profile_key)
