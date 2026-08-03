"""useraccount 插件 — 普通用户的通用 ID 自助管理。

允许普通用户通过指令自行注册通用 ID、绑定/解绑平台账号。

子命令:
  useraccount register [别名]   — 创建通用 ID 并绑定当前账号 (可选设置别名)
  useraccount link <通用ID>     — 请求将当前账号绑定到已有通用 ID
  useraccount confirm <通用ID> <确认码> — 确认 link 请求
  useraccount unlink            — 将当前账号从通用 ID 解绑
  useraccount alias [别名]      — 设置/清除当前通用 ID 的别名 (仅供展示)
  useraccount info              — 查看当前账号的绑定信息
"""

import secrets
import time
from typing import NoReturn

from nonebot import on_command, logger, require
from nonebot.adapters import Bot, Event, Message
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
from nonebot.permission import SUPERUSER

from .config import load_pending_links, save_pending_links, PendingLink

require("bbot_api")
from ..bbot_api import get_raw_user_id
from ..bbot_api.profile_link import get_profile_link_manager
from ..bbot_api.profile_link.profile_link import ProfileLinkManager, UserProfile


# ── 指令定义 ──────────────────────────────────────────

useraccount_cmd = on_command("useraccount", priority=1)


@useraccount_cmd.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()) -> None:
    manager: ProfileLinkManager = get_profile_link_manager()
    cmd_args: list[str] = args.extract_plain_text().strip().split()

    if not cmd_args:
        await useraccount_cmd.finish(
            "用法:\n"
            "useraccount register [别名] - 创建通用 ID 并绑定当前账号 (可选设置别名)\n"
            "useraccount link <通用ID>  - 请求绑定到已有通用 ID\n"
            "useraccount confirm <通用ID> <确认码> - 确认 link 请求\n"
            "useraccount unlink         - 从通用 ID 解绑当前账号\n"
            "useraccount alias [别名]   - 设置/清除你的通用 ID 别名 (仅供展示)\n"
            "useraccount info           - 查看当前账号的绑定信息"
        )

    try:
        action: str = cmd_args[0]

        if action == "register":
            alias: str | None = cmd_args[1] if len(cmd_args) > 1 else None
            await _handle_register(manager, bot, event, alias)
        elif action == "link":
            if len(cmd_args) < 2:
                await useraccount_cmd.finish("用法: useraccount link <通用ID>")
            await _handle_link(manager, bot, event, cmd_args[1])
        elif action == "confirm":
            if len(cmd_args) < 3:
                await useraccount_cmd.finish("用法: useraccount confirm <通用ID> <确认码>")
            await _handle_confirm(manager, bot, event, cmd_args[1], cmd_args[2])
        elif action == "unlink":
            force: bool = "--force" in cmd_args
            await _handle_unlink(manager, bot, event, force=force)
        elif action == "alias":
            alias: str | None = cmd_args[1] if len(cmd_args) > 1 else None
            await _handle_alias(manager, bot, event, alias)
        elif action == "info":
            await _handle_info(manager, bot, event)
        else:
            await useraccount_cmd.finish(f"未知操作: {action}\n使用 useraccount 查看帮助")

    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"useraccount 错误: {e}")
        await useraccount_cmd.finish(f"错误: {e}")


# ── 子命令处理 ────────────────────────────────────────

def _get_current_raw_id(event: Event) -> str:
    """获取当前事件发送者的原始平台用户 ID。"""
    return get_raw_user_id(event)


async def _handle_register(
    manager: ProfileLinkManager,
    bot: Bot,
    event: Event,
    alias: str | None = None,
) -> NoReturn:
    """register: 创建通用 ID 并绑定当前账号。"""
    raw_id: str = _get_current_raw_id(event)

    # 检查是否已绑定
    existing: UserProfile | None = manager.find_user_by_linked_id(raw_id)
    if existing:
        await useraccount_cmd.finish(
            f"你的账号 ({raw_id}) 已绑定到通用 ID '{existing.profile_label}'。\n"
            f"如需解绑请使用: useraccount unlink"
        )

    # 生成通用 ID
    profile_id: str = manager.generate_user_id()

    # 创建 profile
    try:
        manager.create_user_profile(profile_id, alias=alias)
    except ValueError as e:
        # 极端情况：ID 冲突或别名冲突
        if "已存在" in str(e):
            profile_id = f"{profile_id}_{secrets.token_hex(2)}"
            manager.create_user_profile(profile_id, alias=alias)
        else:
            await useraccount_cmd.finish(f"注册失败: {e}")

    # 绑定当前用户
    manager.link_user_id(profile_id, raw_id)
    manager.save()

    if alias:
        await useraccount_cmd.finish(
            f"✅ 注册成功！\n"
            f"通用 ID: {profile_id} (别名: {alias})\n"
            f"已绑定: {raw_id}\n\n"
            f"你可以使用此通用 ID 在其它平台绑定同一账号:\n"
            f"  useraccount link {profile_id}"
        )
    else:
        await useraccount_cmd.finish(
            f"✅ 注册成功！\n"
            f"通用 ID: {profile_id}\n"
            f"已绑定: {raw_id}\n\n"
            f"你可以使用此通用 ID 在其它平台绑定同一账号:\n"
            f"  useraccount link {profile_id}"
        )


async def _handle_link(
    manager: ProfileLinkManager,
    bot: Bot,
    event: Event,
    target_profile_id: str,
) -> NoReturn:
    """link: 请求将当前账号绑定到已有通用 ID。"""
    raw_id: str = _get_current_raw_id(event)

    # 检查当前账号是否已绑定
    existing: UserProfile | None = manager.find_user_by_linked_id(raw_id)
    if existing:
        await useraccount_cmd.finish(
            f"你的账号 ({raw_id}) 已绑定到通用 ID '{existing.profile_label}'。\n"
            f"如需解绑请使用: useraccount unlink"
        )

    # 检查目标通用 ID 是否存在
    profile: UserProfile | None = manager.get_user_profile(target_profile_id)
    if not profile:
        await useraccount_cmd.finish(f"通用 ID '{target_profile_id}' 不存在。请检查后重试。")

    target_label: str = _profile_label(profile)

    # 检查当前账号是否已在待确认列表中
    pending: dict[str, PendingLink] = load_pending_links()
    for token, pl in list(pending.items()):
        if pl.raw_id == raw_id and pl.profile_id == target_profile_id:
            await useraccount_cmd.finish(
                f"已有一个待确认的绑定请求 (确认码: {token})。\n"
                f"请联系已在通用 ID '{target_label}' 下的用户执行:\n"
                f"  useraccount confirm {target_profile_id} {token}"
            )

    # 生成确认码
    token: str = secrets.token_hex(6)  # 12 位十六进制
    expires_at: int = int(time.time()) + 300  # 5 分钟有效

    pending[token] = PendingLink(
        token=token,
        profile_id=target_profile_id,
        raw_id=raw_id,
        created_at=int(time.time()),
        expires_at=expires_at,
    )
    save_pending_links(pending)

    await useraccount_cmd.finish(
        f"📋 绑定请求已创建，确认码有效期为 5 分钟。\n\n"
        f"确认码: {token}\n"
        f"目标通用 ID: {target_label}\n\n"
        f"请联系已在通用 ID '{target_label}' 下的用户执行:\n"
        f"  useraccount confirm {target_profile_id} {token}"
    )


async def _handle_confirm(
    manager: ProfileLinkManager,
    bot: Bot,
    event: Event,
    target_profile_id: str,
    token: str,
) -> NoReturn:
    """confirm: 确认 link 请求。"""
    raw_id: str = _get_current_raw_id(event)

    # SUPERUSER 可以直接确认任何请求
    is_superuser: bool = await SUPERUSER(bot, event)
    if not is_superuser:
        # 检查确认者是否在目标通用 ID 下
        confirmer_profile: UserProfile | None = manager.find_user_by_linked_id(raw_id)
        if not confirmer_profile or confirmer_profile.name != target_profile_id:
            target_p = manager.get_user_profile(target_profile_id)
            await useraccount_cmd.finish(
                f"你没有权限确认此请求。只有已在通用 ID '{_profile_label(target_p) if target_p else target_profile_id}' 下的用户"
                f"或管理员才能确认。"
            )

    # 查找确认码
    pending: dict[str, PendingLink] = load_pending_links()
    pl: PendingLink | None = pending.get(token)
    if not pl:
        await useraccount_cmd.finish("确认码无效或已过期。")

    if pl.profile_id != target_profile_id:
        await useraccount_cmd.finish(f"确认码与通用 ID 不匹配。")

    if pl.expires_at < time.time():
        del pending[token]
        save_pending_links(pending)
        await useraccount_cmd.finish("确认码已过期，请重新发起 link 请求。")

    # 检查要绑定的账号是否已被绑定
    existing: UserProfile | None = manager.find_user_by_linked_id(pl.raw_id)
    if existing:
        del pending[token]
        save_pending_links(pending)
        await useraccount_cmd.finish(
            f"要绑定的账号 ({pl.raw_id}) 已被绑定到 '{existing.profile_label}'，无法重复绑定。"
        )

    # 执行绑定
    try:
        manager.link_user_id(pl.profile_id, pl.raw_id)
    except ValueError as e:
        del pending[token]
        save_pending_links(pending)
        await useraccount_cmd.finish(f"绑定失败: {e}")

    # 清理确认码
    del pending[token]
    save_pending_links(pending)
    manager.save()

    target_p = manager.get_user_profile(pl.profile_id)
    await useraccount_cmd.finish(
        f"✅ 绑定成功！\n"
        f"账号 {pl.raw_id} 已绑定到通用 ID '{_profile_label(target_p) if target_p else pl.profile_id}'。"
    )


async def _handle_unlink(
    manager: ProfileLinkManager,
    bot: Bot,
    event: Event,
    *,
    force: bool = False,
) -> NoReturn:
    """unlink: 将当前账号从通用 ID 解绑。"""
    raw_id: str = _get_current_raw_id(event)

    profile: UserProfile | None = manager.find_user_by_linked_id(raw_id)
    if not profile:
        await useraccount_cmd.finish(f"你的账号 ({raw_id}) 未绑定任何通用 ID。")

    # 检查是否是该通用 ID 下的最后一个绑定
    if len(profile.linked_ids) <= 1 and not force:
        await useraccount_cmd.finish(
            f"你的账号 ({raw_id}) 是通用 ID '{profile.profile_label}' 下的最后一个绑定。\n"
            f"解绑后该通用 ID 将被删除。\n"
            f"如需继续，请使用: useraccount unlink --force"
        )

    try:
        manager.unlink_user_id(profile.name, raw_id)
    except ValueError as e:
        await useraccount_cmd.finish(f"解绑失败: {e}")

    # 如果通用 ID 下没有绑定了，删除它
    if not profile.linked_ids:
        manager.delete_user_profile(profile.name)

    manager.save()

    await useraccount_cmd.finish(
        f"✅ 已解绑！\n"
        f"账号 {raw_id} 已从通用 ID '{profile.profile_label}' 解除绑定。"
    )


async def _handle_alias(
    manager: ProfileLinkManager,
    bot: Bot,
    event: Event,
    alias: str | None,
) -> NoReturn:
    """alias: 设置或清除当前账号通用 ID 的别名 (仅供展示)。"""
    raw_id: str = _get_current_raw_id(event)

    profile: UserProfile | None = manager.find_user_by_linked_id(raw_id)
    if not profile:
        await useraccount_cmd.finish(
            f"你的账号 ({raw_id}) 未绑定任何通用 ID。\n"
            f"使用 useraccount register 创建一个。"
        )

    try:
        manager.set_user_alias(profile.name, alias)
    except ValueError as e:
        await useraccount_cmd.finish(f"设置别名失败: {e}")

    manager.save()

    if profile.alias:
        await useraccount_cmd.finish(
            f"✅ 已设置别名: {profile.alias}\n"
            f"通用 ID: {profile.name}\n"
            f"别名仅用于展示，内部数据仍以通用 ID 为准。"
        )
    else:
        await useraccount_cmd.finish(
            f"✅ 已清除别名。\n"
            f"展示将回退到通用 ID: {profile.name}"
        )


async def _handle_info(
    manager: ProfileLinkManager,
    bot: Bot,
    event: Event,
) -> NoReturn:
    """info: 查看当前账号的绑定信息。"""
    raw_id: str = _get_current_raw_id(event)

    profile: UserProfile | None = manager.find_user_by_linked_id(raw_id)
    if not profile:
        await useraccount_cmd.finish(
            f"你的账号 ({raw_id}) 未绑定任何通用 ID。\n"
            f"使用 useraccount register 创建一个。"
        )

    lines: list[str]
    if profile.alias:
        lines = [
            f"通用 ID: {profile.name} (别名: {profile.alias})",
            f"当前账号: {raw_id}",
            f"已绑定账号 ({len(profile.linked_ids)}):",
        ]
    else:
        lines = [
            f"通用 ID: {profile.name}",
            f"当前账号: {raw_id}",
            f"已绑定账号 ({len(profile.linked_ids)}):",
        ]
    for lid in profile.linked_ids:
        marker: str = " ← 当前账号" if lid == raw_id else ""
        lines.append(f"  - {lid}{marker}")

    await useraccount_cmd.finish("\n".join(lines))


# ── 辅助函数 ──────────────────────────────────────────

def _profile_label(profile: UserProfile | None) -> str:
    """生成通用 ID 的展示标签；有别名时同时列出别名。"""
    return profile.profile_label if profile else ""

def _generate_profile_id(raw_id: str) -> str:
    """根据原始 ID 生成一个可读的通用 ID。"""
    # 去掉平台前缀
    for prefix in ("dc_", "group_", "u_", "qquser_", "qqgroup_", "mc_"):
        if raw_id.startswith(prefix):
            core: str = raw_id[len(prefix):]
            break
    else:
        core = raw_id

    # 取前 8 位加上随机后缀
    short: str = core[:8]
    suffix: str = secrets.token_hex(3)  # 6 位十六进制
    return f"user_{short}_{suffix}"

def get_help(bot,event)->str|None:
    if isinstance(bot, Bot):
        return "useraccount 管理帐户绑定 (可认领旧数据或绑定不同平台帐户)"
    else:
        return None