from .profile_link import get_profile_link_manager

def get_user_alias(profile_id: str) -> str | None:
    """获取用户通用 ID 的别名；无别名时返回 None，由调用端处理。"""
    manager = get_profile_link_manager()
    profile = manager.get_user_profile(profile_id)
    return profile.alias if profile else None

def get_group_alias(profile_id: str) -> str | None:
    """获取群通用 ID 的别名；无别名时返回 None，由调用端处理。"""
    manager = get_profile_link_manager()
    profile = manager.get_group_profile(profile_id)
    return profile.alias if profile else None

def resolve_user_by_ref(ref: str) -> str | None:
    """按通用 ID 或别名反查用户通用 ID；找不到时返回 None。

    供其他插件调用：传入通用 ID 或别名，返回对应的通用 ID（内部键）。
    """
    manager = get_profile_link_manager()
    profile = manager.resolve_user_profile(ref)
    return profile.name if profile else None

def resolve_group_by_ref(ref: str) -> str | None:
    """按通用 ID 或别名反查群通用 ID；找不到时返回 None。

    供其他插件调用：传入通用 ID 或别名，返回对应的通用 ID（内部键）。
    """
    manager = get_profile_link_manager()
    profile = manager.resolve_group_profile(ref)
    return profile.name if profile else None

def resolve_user_by_raw_id(raw_id:str):
    manager = get_profile_link_manager()
    resolved = manager.resolve_user_id(raw_id)
    return resolved